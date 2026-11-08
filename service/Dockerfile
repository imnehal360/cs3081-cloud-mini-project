
FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    HF_HUB_OFFLINE=1 \
    TRANSFORMERS_OFFLINE=1 \
    MODEL_VERSION=v1 \
    MAX_NEW_TOKENS=80

# Install CPU-only PyTorch
RUN pip install --no-cache-dir \
    torch==2.5.1 \
    --index-url https://download.pytorch.org/whl/cpu

# Install application dependencies
COPY service/requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir \
    -r /app/requirements.txt

# Copy source code only (no model weights)
COPY service/ /app/service/

EXPOSE 8000

CMD ["uvicorn", "service.main:app", "--host", "0.0.0.0", "--port", "8000"]
