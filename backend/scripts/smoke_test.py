from pathlib import Path

from fastapi.testclient import TestClient
from PIL import Image

from app.main import app

client = TestClient(app)
print(client.get("/api/health").json())
created = client.post("/api/projects", json={"name": "Demo plot", "occupancy": "residential"}).json()
print("project", created["id"], created["status"])

img = Path("demo.png")
Image.new("RGB", (40, 24), (200, 200, 200)).save(img)
upload = client.post(
    f"/api/projects/{created['id']}/upload",
    files={"file": ("plot.png", img.read_bytes(), "image/png")},
)
print("upload", upload.status_code, upload.json().get("status"))

detail = client.get(f"/api/projects/{created['id']}").json()
print("rules", len((detail.get("matched_rules") or {}).get("skills") or []))

confirmed = client.post(
    f"/api/projects/{created['id']}/confirm-rules",
    json={"approved": True, "notes": "ok"},
).json()
print("confirm", confirmed["status"], confirmed.get("dxf_path"))
print("nbc", len(client.get("/api/knowledge/nbc").json()))
