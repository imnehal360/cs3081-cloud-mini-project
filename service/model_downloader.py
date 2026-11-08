
import hashlib
import os
import shutil
import tempfile
import urllib.request
import zipfile
from pathlib import Path

REPO = "imnehal360/cs3081-cloud-mini-project"
RELEASE_TAG = "model-v1"


def download_model():
    version = os.getenv("MODEL_VERSION", "v1")

    if version not in {"v1", "v2"}:
        raise ValueError("MODEL_VERSION must be v1 or v2")

    model_dir = Path(f"/tmp/models/{version}")
    archive_name = f"pythia-{version}.zip"

    base_url = (
        f"https://github.com/{REPO}/releases/download/"
        f"{RELEASE_TAG}"
    )

    archive_url = f"{base_url}/{archive_name}"
    checksum_url = f"{archive_url}.sha256"

    model_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as temp_dir:
        archive_path = Path(temp_dir) / archive_name
        checksum_path = Path(temp_dir) / f"{archive_name}.sha256"

        print(f"Downloading {archive_url}", flush=True)

        urllib.request.urlretrieve(archive_url, archive_path)
        urllib.request.urlretrieve(checksum_url, checksum_path)

        actual_hash = hashlib.sha256(
            archive_path.read_bytes()
        ).hexdigest()

        expected_hash = checksum_path.read_text(
            encoding="utf-8"
        ).split()[0]

        if actual_hash != expected_hash:
            raise ValueError("Model checksum mismatch")

        # Extract only after checksum verification.
        with zipfile.ZipFile(archive_path) as archive:
            for entry in archive.infolist():
                path = Path(entry.filename)

                if path.is_absolute() or ".." in path.parts:
                    raise ValueError("Unsafe ZIP entry")

            archive.extractall(temp_dir)

        source = Path(temp_dir) / version

        if not source.exists():
            raise FileNotFoundError(
                f"Expected model directory missing: {source}"
            )

        if model_dir.exists():
            shutil.rmtree(model_dir)

        shutil.copytree(source, model_dir)

    print(f"Model {version} ready at {model_dir}", flush=True)
    return str(model_dir)
