# RetinaGuard: AI-Powered Diabetic Retinopathy Screening System

RetinaGuard is a full-stack clinical decision-support platform for automated Diabetic Retinopathy (DR) screening and triage. It combines deterministic fundus image quality verification, deep learning classification (EfficientNet-B0), lesion detection, explainability (Grad-CAM), and a modern clinical dashboard.

---

## 🌟 Key Features

- **Automated Image Quality Gate**: Rule-based OpenCV quality assessment (blur, illumination, contrast, FOV, artifacts) preventing ungradable scans from reaching the classifier.
- **Deep Learning DR Grading**: EfficientNet-B0 model classifying retinal fundus images into 5 ICDR severity levels:
  - 0: No DR
  - 1: Mild NPDR
  - 2: Moderate NPDR (Referable)
  - 3: Severe NPDR (Referable)
  - 4: Proliferative DR (Referable)
- **Clinical Explainability**: Grad-CAM heatmaps highlighting pathological regions guiding clinical attention.
- **Interactive Clinical Dashboard**: React + TypeScript frontend featuring patient worklists, screening history, clinical review queue, and analytics.
- **RESTful API**: Fast, asynchronous FastAPI backend with automated validation and reporting.

---

## 🏗️ Architecture

```
RetinaGuard/
├── backend/            # FastAPI REST backend and ML inference services
│   ├── routes/         # API endpoints (screening, patients, reviews, analytics)
│   ├── services/       # Quality, Preprocessing, Classification, Explainability
│   └── tests/          # Integration & unit test suites
├── frontend/           # Modern React + Vite + Tailwind CSS clinical UI
│   ├── src/components/ # Medical UI components (Grad-CAM viewer, lesion maps)
│   └── src/pages/      # Screening, Review Queue, Patient Worklist, Analytics
├── ml/                 # Model training, evaluation, and dataset curation scripts
├── models/             # PyTorch trained model weights (EfficientNet-B0 checkpoints)
├── data/               # Processed metadata CSVs and test samples
└── docs/               # Technical documentation, experiment logs, and evaluations
```

---

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- Node.js 18+ and npm

### 1. Backend Setup
```bash
cd backend
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```
API Documentation will be available at `http://localhost:8000/docs`.

### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:5173` in your browser.

---

## 🧪 Testing

Run backend automated verification:
```bash
cd backend
python verify_backend.py
```

---

## 📄 License
This project is licensed under the MIT License.
