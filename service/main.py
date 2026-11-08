
import os
import json
import socket
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel

try:
    from service.model_runner import ModelRunner
except ModuleNotFoundError:
    from model_runner import ModelRunner


try:
    from service.model_downloader import download_model
except ModuleNotFoundError:
    from model_downloader import download_model


runner = None
ready = False

ALLOWED_INTENTS = {
    "alarm_set",
    "alarm_query",
    "calendar_set",
    "calendar_query",
    "calendar_remove",
    "weather_query",
    "datetime_query",
    "recommendation_events",
}

REQUIRED_KEYS = {"intent", "date", "time", "place"}


@asynccontextmanager
async def lifespan(app: FastAPI):
    global runner, ready

    model_path = download_model()
    runner = ModelRunner(model_path)
    ready = True

    yield

    ready = False
    runner = None


app = FastAPI(lifespan=lifespan)


class ParseRequest(BaseModel):
    text: str


@app.get("/healthz")
def healthz():
    return {"status": "alive"}


@app.get("/readyz")
def readyz(response: Response):
    if not ready:
        response.status_code = 503
        return {"status": "not_ready"}

    return {"status": "ready"}


@app.post("/parse")
def parse(request: ParseRequest, response: Response):
    if not ready or runner is None:
        raise HTTPException(status_code=503, detail="Model not ready")

    max_tokens = int(os.getenv("MAX_NEW_TOKENS", "80"))
    model_version = os.getenv("MODEL_VERSION", "v1")

    raw = runner.predict(request.text, max_tokens)

    if os.getenv("FAULT_INJECT", "0") == "1":
        raw = "not json"

    try:
        parsed = json.loads(raw)

        if not isinstance(parsed, dict):
            raise ValueError("Output must be a JSON object")

        if set(parsed.keys()) != REQUIRED_KEYS:
            raise ValueError("Incorrect JSON keys")

        if parsed["intent"] not in ALLOWED_INTENTS:
            raise ValueError("Invalid intent")

        for field in ("date", "time", "place"):
            value = parsed[field]
            if value is not None and not isinstance(value, str):
                raise ValueError(f"Invalid {field}")

    except (json.JSONDecodeError, ValueError, TypeError):
        return Response(
            content='{"error":"invalid_model_output"}',
            status_code=500,
            media_type="application/json",
        )

    response.headers["X-Model-Version"] = model_version
    response.headers["X-Served-By"] = os.getenv(
        "HOSTNAME", socket.gethostname()
    )

    return parsed
