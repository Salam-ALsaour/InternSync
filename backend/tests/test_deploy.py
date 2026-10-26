"""The Space deployment script (Increment 2 design, Section 10): what it uploads and where the API will be served."""
import importlib.util
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "deploy_space.py"
spec = importlib.util.spec_from_file_location("deploy_space", SCRIPT)
deploy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(deploy)


def test_stage_holds_what_the_image_is_built_from(tmp_path):
    deploy.stage(tmp_path)
    readme = (tmp_path / "README.md").read_text(encoding="utf-8")
    assert "sdk: docker" in readme and "app_port: 7860" in readme
    for name in ("Dockerfile", "requirements.txt", "requirements-ai.txt", "alembic.ini", "app/main.py",
                 "alembic/versions/0003_row_level_security.py"):
        assert (tmp_path / name).is_file(), name
    assert not list(tmp_path.rglob("__pycache__")) and not (tmp_path / "tests").exists()
    assert not (tmp_path / ".env").exists()


def test_space_address():
    assert deploy.space_url("Salam_ALsaour/InternSync.API") == "https://salam-alsaour-internsync-api.hf.space"


def test_missing_token_stops_before_any_call(monkeypatch, capsys):
    monkeypatch.delenv("HF_TOKEN", raising=False)
    monkeypatch.setenv("HF_SPACE", "owner/internsync-api")
    assert deploy.main() == 2
    assert "HF_TOKEN" in capsys.readouterr().err
