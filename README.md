# MaizeGuard Rwanda

MaizeGuard is a maize quality screening product for post-harvest decision support. The application lets a user upload a maize image and returns a quality category, confidence score, risk level, recommended action, and farmer-friendly recommendation.

The final model classifies four visible maize quality classes:

- `good`
- `broken`
- `impurity`
- `mold_risk`

The deployed app may also show `Needs review` when the image is unclear, low confidence, poor quality, or when `broken` and `mold_risk` are too close to separate safely.

## Submission Links

- Deployed frontend: https://maizeguard-frontend.vercel.app
- Deployed backend API: https://maizeguard-backend-419n.onrender.com
- Demo video: https://youtu.be/0U93bL54p_g

## Core Functionality

- Upload a maize image through the web interface.
- Send the image to the FastAPI PyTorch model server.
- Predict the maize quality class using a MobileNetV3 transfer-learning model.
- Return confidence, probabilities, risk level, action, and recommendation.
- Use `Needs review` for uncertain or unsafe predictions.
- Provide testing evidence through saved metrics, plots, confusion matrices, and audit outputs.

## Technology Stack

- Frontend: Next.js, React, TypeScript, Tailwind CSS
- Backend: FastAPI, Python, PyTorch, timm, Pillow
- Model: MobileNetV3 Large with ImageNet transfer learning
- Training environment: Kaggle notebook
- Deployment: Vercel frontend and Render backend

## Project Structure

```text
capstone-backend/
  model_server/
    main.py
    pytorch_main.py
    model_exports/
      maizeguard_public_best_model.pt
      maizeguard_model_metadata.json
      class_names.json
  notebooks/
    maizeguard_final_submission_notebook.ipynb
  reports/models/
    model_metrics_summary.csv
    classification_report_raw_argmax.csv
    09_normalized_confusion_matrix.png
    broken_mold_audit_pages/
  scripts/
  docs/
  README.md
  render.yaml
  start.sh
```

The frontend is kept in the companion `capstone-frontend` project and calls the backend through its Next.js `/api/analyze` route.

## Related Files

Important backend/model files:

- `model_server/pytorch_main.py` - loads the PyTorch model and exposes `/predict`.
- `model_server/main.py` - compatibility entrypoint that re-exports the FastAPI app.
- `model_server/model_exports/maizeguard_public_best_model.pt` - final trained model checkpoint.
- `model_server/model_exports/maizeguard_model_metadata.json` - model settings, image size, normalization, safety thresholds, and training summary.
- `model_server/model_exports/class_names.json` - class order used by the model.
- `notebooks/maizeguard_final_submission_notebook.ipynb` - final Kaggle training and export notebook.
- `reports/models/` - final testing results, plots, metrics, predictions, and audit files.

Important frontend files:

- `app/page.tsx` - upload interface and result display.
- `app/api/analyze/route.ts` - proxy route that forwards uploaded images to the backend model API.
- `app/layout.tsx` - app metadata and favicon setup.

## Local Installation and Run

### 1. Get the project

```bash
cd capstone-backend
```

### 2. Run the backend locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
./start.sh
```

Backend URLs:

```text
http://127.0.0.1:8000
http://127.0.0.1:8000/docs
http://127.0.0.1:8000/health
```

### 3. Run the frontend locally

From the frontend project folder:

```bash
cd ../capstone-frontend
npm install
cp .env.example .env.local
```

Set the local backend URL in `.env.local`:

```text
MODEL_API_URL=http://127.0.0.1:8000
```

Start the frontend:

```bash
npm run dev
```

Open:

```text
http://localhost:3000
```

## API Usage

Prediction endpoint:

```text
POST /predict
form-data field: image
```

Example response fields:

```json
{
  "label": "good",
  "raw_label": "good",
  "confidence": 0.85,
  "confidence_percent": 85.0,
  "needs_review": false,
  "probabilities": {
    "good": 0.85,
    "broken": 0.14,
    "impurity": 0.0,
    "mold_risk": 0.01
  },
  "risk": "Low",
  "action": "Store safely or prepare for sale",
  "recommendation": "The maize appears clean. Store in a dry place and monitor normally."
}
```

## Deployment Plan and Execution

### Backend on Render

Render settings:

```text
Root directory: capstone-backend
Build command: pip install -r requirements.txt
Start command: ./start.sh
Health check path: /
```

Recommended backend environment variables:

```text
CONFIDENCE_THRESHOLD=0.65
TOP2_MARGIN_THRESHOLD=0.15
BATCH_INFERENCE_ENABLED=false
TORCH_NUM_THREADS=1
CORS_ORIGINS=http://localhost:3000,https://maizeguard-frontend.vercel.app,https://maizeguard-frontend-70xyc87wl-honorine22s-projects.vercel.app
```

Backend verification:

```text
https://maizeguard-backend-419n.onrender.com/health
```

### Frontend on Vercel

Vercel settings:

```text
Root directory: capstone-frontend
Build command: npm run build
Output: Next.js default
```

Frontend environment variable:

```text
MODEL_API_URL=https://maizeguard-backend-419n.onrender.com
```

After changing Vercel environment variables, redeploy the frontend. Existing deployments do not automatically use new environment values.

## Testing Results and Strategies

Testing evidence is saved in `reports/models/`.

### 1. Functional testing

The main workflow was tested by uploading maize images through the frontend and verifying that the backend returned:

- predicted class
- confidence score
- probability distribution
- risk level
- action
- recommendation
- `Needs review` when appropriate

Relevant files:

- `reports/models/test_predictions_and_errors_raw_argmax.csv`
- `reports/models/classification_report_raw_argmax.csv`
- `reports/models/model_metrics_summary.csv`

### 2. Different data values

The model was tested on different maize categories:

- clean/good maize
- broken kernels
- impurity-contaminated maize
- visible mold-risk maize
- unclear broken-versus-mold cases

Relevant files:

- `reports/models/03_sample_images_by_class.png`
- `reports/models/11_mistakes_raw_argmax.png`
- `reports/models/broken_mold_test_predictions.csv`

### 3. Edge case and safety testing

The deployment logic flags uncertain predictions as `Needs review` when confidence is low, the top-two margin is small, image quality is poor, or broken and mold-risk probabilities are too close. This prevents the system from giving misleading confident advice on unclear images.

Relevant files:

- `reports/models/confidence_summary_by_class.csv`
- `reports/models/broken_mold_pair_confusion.csv`
- `reports/models/broken_mold_audit_pages/`

### 4. Performance and environment testing

The model was trained and evaluated in Kaggle, then exported to the FastAPI backend. The application was prepared for deployment with:

- Kaggle notebook training/evaluation
- local backend API checks
- Next.js production build checks
- Render backend deployment settings
- Vercel frontend deployment settings

The backend uses single-image inference by default on Render to reduce memory and CPU load on the free instance.

## Final Model Results

Final test results from `reports/models/model_metrics_summary.csv`:

```text
Official test accuracy: 0.9545
Official test macro F1: 0.9556
Official test broken/mold F1: 0.9375
Test samples: 44
Mistakes: 2
```

Important visual results:

- `reports/models/08_confusion_matrix_raw_argmax.png`
- `reports/models/09_normalized_confusion_matrix.png`
- `reports/models/10_per_class_metrics.png`
- `reports/models/07_validation_accuracy_macro_f1.png`

## Analysis of Results

The project achieved the main proposal objective: building a working maize quality screening product that connects an image upload interface to a trained machine learning model and returns practical post-harvest recommendations.

The strongest results were achieved on clear examples of `good`, `impurity`, and `mold_risk` classes. The final official test accuracy was `95.45%`, and the macro F1 score was `0.9556`, showing strong overall class balance.

The most important limitation is the visual overlap between `broken` and `mold_risk`. Some maize kernels can show both physical damage and dark or decayed appearance. For that reason, the system does not force every uncertain image into a confident class. Instead, it uses `Needs review` as a safety outcome and includes a human label audit process in the final notebook.

The final model therefore meets the product objective for visible maize quality screening, while also clearly identifying the remaining data-quality challenge.

## Discussion

The main milestones were important because they moved the project from a model experiment to a usable product:

1. Dataset preparation created a consistent four-class maize quality structure.
2. Model training produced a deployable MobileNetV3 classifier.
3. Evaluation generated confusion matrices, classification reports, and prediction logs.
4. The human audit step addressed the broken-versus-mold-risk label overlap responsibly.
5. Backend deployment made the model usable through an API.
6. Frontend deployment made the system accessible to users through a browser.

The impact of the result is that farmers, cooperatives, students, or storage managers can quickly screen visible maize quality from an image and receive an understandable recommendation. The product is not a laboratory aflatoxin test and should not replace official food safety inspection, but it can support early awareness and better post-harvest decisions.

## Recommendations and Future Work

Recommendations to users and the community:

- Use clear, close-up images of shelled maize on a plain surface.
- Treat `mold_risk` as a visible warning, not a laboratory diagnosis.
- Use `Needs review` seriously when the image is unclear or the model is uncertain.
- Do not store maize that shows visible mold-risk signs without further checking.
- Continue sorting broken kernels and removing impurities before storage or sale.

Future work:

- Collect more local Rwandan maize images.
- Add expert-reviewed labels for difficult broken-versus-mold-risk cases.
- Improve mobile camera guidance inside the app.
- Add Kinyarwanda language support.
- Add offline or low-connectivity mobile support.
- Evaluate the model on larger real-world cooperative and market datasets.
- Add a formal expert review workflow for uncertain predictions.