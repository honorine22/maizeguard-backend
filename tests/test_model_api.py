import io

import numpy as np
from fastapi.testclient import TestClient
from PIL import Image

import model_server.pytorch_main as api


client = TestClient(api.app)


def make_image_bytes(color=(184, 145, 72), size=(256, 256), textured=True):
    """Create an in-memory test image with maize-like colour and texture."""
    if textured:
        rng = np.random.default_rng(42)
        base = np.full((size[1], size[0], 3), color, dtype=np.int16)
        noise = rng.integers(-35, 36, size=base.shape, dtype=np.int16)
        array = np.clip(base + noise, 0, 255).astype(np.uint8)
        image = Image.fromarray(array)
    else:
        image = Image.new("RGB", size, color)

    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer


def post_image(image_bytes):
    return client.post(
        "/predict",
        files={"image": ("sample.png", image_bytes, "image/png")},
    )


def test_health_endpoint_reports_ready_model():
    response = client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ready"
    assert payload["model"] == api.MODEL_NAME
    assert payload["classes"] == ["good", "broken", "impurity", "mold_risk"]
    assert payload["image_size"] == api.IMG_SIZE


def test_recommendation_for_supported_classes():
    good = api.recommendation_for("good", needs_review=False)
    mold = api.recommendation_for("mold_risk", needs_review=False)

    assert good["risk"] == "Low"
    assert "Store safely" in good["action"]
    assert mold["risk"] == "High"
    assert "checking" in mold["action"].lower()


def test_recommendation_for_uncertain_or_unsupported_images():
    review = api.recommendation_for("good", needs_review=True)
    unsupported = api.recommendation_for("unsupported_image", needs_review=False)

    assert review["risk"] == "Needs review"
    assert "Retake" in review["recommendation"]
    assert unsupported["risk"] == "Unsupported image"
    assert "Upload maize image" in unsupported["action"]


def test_needs_review_for_low_confidence_or_small_margin():
    assert api.needs_review(np.array([0.4, 0.3, 0.2, 0.1]), confidence=0.4)
    assert api.needs_review(np.array([0.51, 0.44, 0.03, 0.02]), confidence=0.51)
    assert not api.needs_review(np.array([0.9, 0.05, 0.03, 0.02]), confidence=0.9)


def test_image_quality_review_flags_tiny_or_blank_images():
    tiny = Image.new("RGB", (80, 80), (180, 145, 80))
    blank = Image.new("RGB", (256, 256), (255, 255, 255))

    tiny_review, tiny_reason = api.image_quality_review(tiny)
    blank_review, blank_reason = api.image_quality_review(blank)

    assert tiny_review
    assert "too small" in tiny_reason
    assert blank_review
    assert "texture" in blank_reason or "blank" in blank_reason


def test_unsupported_image_reason_flags_non_maize_colours():
    blue_texture = Image.open(make_image_bytes(color=(25, 70, 210), textured=True)).convert("RGB")

    reason = api.unsupported_image_reason(blue_texture)

    assert reason is not None
    assert "maize" in reason.lower()


def test_predict_returns_expected_shape_for_good_maize(monkeypatch):
    def fake_predict_views(_image):
        return (
            np.array([0.91, 0.04, 0.03, 0.02]),
            [{"view": "full", "label": "good", "confidence": 0.91}],
        )

    monkeypatch.setattr(api, "predict_views", fake_predict_views)
    monkeypatch.setattr(api, "image_quality_review", lambda _image: (False, None))
    monkeypatch.setattr(api, "unsupported_image_reason", lambda _image: None)

    response = post_image(make_image_bytes())

    assert response.status_code == 200
    payload = response.json()
    assert payload["label"] == "good"
    assert payload["raw_label"] == "good"
    assert payload["confidence"] == 0.91
    assert payload["confidence_percent"] == 91.0
    assert payload["needs_review"] is False
    assert payload["risk"] == "Low"
    assert payload["action"] == "Store safely or prepare for sale"
    assert payload["inference_view"] == "full_image"
    assert payload["view_count"] == 1
    assert set(payload["probabilities"]) == set(api.CLASS_NAMES)


def test_predict_keeps_uncertain_maize_prediction_as_model_class(monkeypatch):
    def fake_predict_views(_image):
        return (
            np.array([0.52, 0.45, 0.02, 0.01]),
            [{"view": "full", "label": "good", "confidence": 0.52}],
        )

    monkeypatch.setattr(api, "predict_views", fake_predict_views)
    monkeypatch.setattr(api, "image_quality_review", lambda _image: (False, None))
    monkeypatch.setattr(api, "unsupported_image_reason", lambda _image: None)

    response = post_image(make_image_bytes())

    assert response.status_code == 200
    payload = response.json()
    assert payload["label"] == "good"
    assert payload["needs_review"] is False
    assert payload["risk"] == "Low"
    assert payload["action"] == "Store safely or prepare for sale"


def test_predict_trusts_high_confidence_maize_class_over_colour_heuristic(monkeypatch):
    def fake_predict_views(_image):
        return (
            np.array([0.0, 0.9935, 0.0, 0.0065]),
            [{"view": "full", "label": "broken", "confidence": 0.9935}],
        )

    monkeypatch.setattr(api, "predict_views", fake_predict_views)
    monkeypatch.setattr(api, "image_quality_review", lambda _image: (False, None))
    monkeypatch.setattr(
        api,
        "unsupported_image_reason",
        lambda _image: "The image does not appear to contain enough maize-like grain color or texture.",
    )

    response = post_image(make_image_bytes(color=(245, 245, 245), textured=True))

    assert response.status_code == 200
    payload = response.json()
    assert payload["label"] == "broken"
    assert payload["raw_label"] == "broken"
    assert payload["confidence"] == 0.9935
    assert payload["needs_review"] is False
    assert payload["review_reason"] is None
    assert payload["risk"] == "Medium"
    assert payload["action"] == "Sort before storage"


def test_predict_returns_unsupported_image_for_non_maize_input(monkeypatch):
    def fake_predict_views(_image):
        return (
            np.array([0.5, 0.28, 0.12, 0.1]),
            [{"view": "full", "label": "good", "confidence": 0.5}],
        )

    monkeypatch.setattr(api, "predict_views", fake_predict_views)
    monkeypatch.setattr(api, "image_quality_review", lambda _image: (False, None))
    monkeypatch.setattr(
        api,
        "unsupported_image_reason",
        lambda _image: "The image does not appear to contain enough maize-like grain color or texture.",
    )

    response = post_image(make_image_bytes(color=(25, 70, 210), textured=True))

    assert response.status_code == 200
    payload = response.json()
    assert payload["label"] == "unsupported_image"
    assert payload["raw_label"] == "good"
    assert payload["needs_review"] is False
    assert payload["risk"] == "Unsupported image"
    assert "does not appear" in payload["review_reason"]
