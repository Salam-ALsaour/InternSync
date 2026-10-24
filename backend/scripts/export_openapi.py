"""Write the OpenAPI document the web app's types are generated from (API specification, Section 6).

    python scripts/export_openapi.py ../frontend/src/api/openapi.json

Development-only routes are left out (ENV=production)."""
import json
import os
import sys
from pathlib import Path

os.environ["ENV"] = "production"
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.main import create_app  # noqa: E402

out = Path(sys.argv[1])
out.write_text(json.dumps(create_app().openapi(), ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
print(f"wrote {out}")
