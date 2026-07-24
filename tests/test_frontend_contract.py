from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_ROOT = BACKEND_ROOT.parent / "capstone-frontend"


def read_frontend_page():
    return (FRONTEND_ROOT / "app" / "page.tsx").read_text(encoding="utf-8")


def test_frontend_project_is_available():
    assert FRONTEND_ROOT.exists()
    assert (FRONTEND_ROOT / "package.json").exists()
    assert (FRONTEND_ROOT / "app" / "page.tsx").exists()


def test_frontend_default_backend_url_matches_final_deployment():
    source = read_frontend_page()

    assert "https://honorineigiraneza-maizeguard-backend.hf.space" in source
    assert "NEXT_PUBLIC_MODEL_API_URL" in source
    assert "/predict" in source


def test_frontend_handles_review_and_unsupported_api_responses():
    source = read_frontend_page()

    assert "needs_review" in source
    assert "review_reason" in source
    assert "unsupported" in source
    assert "Upload a clear maize image" in source


def test_frontend_favicon_exists_for_deployment():
    assert (FRONTEND_ROOT / "public" / "favicon.ico").exists()
