FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=7860
ENV TORCH_NUM_THREADS=1
ENV BATCH_INFERENCE_ENABLED=false
ENV CORS_ORIGINS=http://localhost:3000,http://localhost:3006,https://maizeguard-frontend.vercel.app,https://maizeguard-frontend-70xyc87wl-honorine22s-projects.vercel.app

WORKDIR /app

RUN apt-get update \
  && apt-get install -y --no-install-recommends libgl1 libglib2.0-0 \
  && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./requirements.txt
COPY model_server/requirements-pytorch.txt ./model_server/requirements-pytorch.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY model_server ./model_server

WORKDIR /app/model_server
EXPOSE 7860
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-7860}"]
