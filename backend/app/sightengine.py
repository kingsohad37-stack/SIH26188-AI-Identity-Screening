import json
from urllib.request import Request, urlopen
from urllib.parse import urlencode

from .config import settings


def analyze_image(path: str) -> dict:
    """Run Sightengine server-side. Missing credentials/failures are fail-soft."""
    if not settings.sightengine_api_user or not settings.sightengine_api_secret:
        return {"available": False, "status": "not_configured", "reason": "Sightengine credentials are not configured."}
    try:
        boundary = b"----sih26188-sightengine"
        with open(path, "rb") as f:
            media = f.read()
        fields = {
            "models": settings.sightengine_models,
            "api_user": settings.sightengine_api_user,
            "api_secret": settings.sightengine_api_secret,
        }
        body = bytearray()
        for key, value in fields.items():
            body.extend(b"--" + boundary + b"\r\n")
            body.extend(f'Content-Disposition: form-data; name="{key}"\r\n\r\n'.encode())
            body.extend(str(value).encode())
            body.extend(b"\r\n")
        body.extend(b"--" + boundary + b"\r\n")
        body.extend(b'Content-Disposition: form-data; name="media"; filename="document.jpg"\r\n')
        body.extend(b"Content-Type: application/octet-stream\r\n\r\n")
        body.extend(media)
        body.extend(b"\r\n--" + boundary + b"--\r\n")
        request = Request(
            "https://api.sightengine.com/1.0/check.json",
            data=bytes(body),
            headers={"Content-Type": f"multipart/form-data; boundary={boundary.decode()}", "User-Agent": "SIH26188/1.0"},
            method="POST",
        )
        with urlopen(request, timeout=8) as response:
            payload = json.loads(response.read().decode("utf-8"))
        if payload.get("status") != "success":
            return {"available": False, "status": "error", "response": payload}
        return {"available": True, "status": "completed", "models": settings.sightengine_models, "response": payload}
    except Exception as exc:
        return {"available": False, "status": "error", "reason": type(exc).__name__}
