# ML Image Processing Service

A modular ML backend for image processing tasks such as denoising,
segmentation, restoration, and other post-render operations.

## Run
```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --host 127.0.0.1 --port 8000