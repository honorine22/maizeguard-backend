# MaizeGuard Model Exports

The FastAPI PyTorch server loads the final Kaggle-trained MobileNetV3 model from this folder.

Required files:

- `maizeguard_public_best_model.pt`
- `maizeguard_model_metadata.json`
- `class_names.json`

Final exported run:

- official test accuracy: `0.9545`
- official test macro F1: `0.9556`
- official test broken/mold F1: `0.9375`
- input size: `320`
- classes: `good`, `broken`, `impurity`, `mold_risk`

Run with:

```bash
uvicorn pytorch_main:app --reload --port 8000
```

The compatibility command below also works and loads the same PyTorch app:

```bash
uvicorn main:app --reload --port 8000
```
