"""File storage backends (Increment 2 design, Section 10): the Supabase adapter against a stand-in of the Storage
API, and the choice of backend from the configuration."""
import importlib.util
import json
import tarfile
from pathlib import Path

import httpx
import pytest

from app.core import files
from app.core.config import get_settings
from app.core.storage_supabase import SupabaseStorage

URL, KEY, BUCKET = "https://abc.supabase.co", "service-key", "internsync-files"


class FakeStorageApi:
    """Just enough of the Supabase Storage API: one private bucket of objects."""

    def __init__(self):
        self.buckets: set[str] = set()
        self.objects: dict[str, bytes] = {}
        self.seen: list[httpx.Request] = []

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.seen.append(request)
        assert request.headers["authorization"] == f"Bearer {KEY}" and request.headers["apikey"] == KEY
        path = request.url.path.removeprefix("/storage/v1/")
        if path == "bucket" and request.method == "POST":
            name = httpx.Response(200, content=request.content).json()["id"]
            if name in self.buckets:
                return httpx.Response(400, json={"statusCode": "409", "error": "Duplicate",
                                                 "message": "The resource already exists"})
            self.buckets.add(name)
            return httpx.Response(200, json={"name": name})
        if path == f"object/list/{BUCKET}":
            return httpx.Response(200, json=self.listing(json.loads(request.content)))
        key = path.removeprefix("object/").removeprefix("authenticated/")
        if request.method == "POST":
            self.objects[key] = request.content
            return httpx.Response(200, json={"Key": key})
        if key not in self.objects:
            return httpx.Response(400, json={"statusCode": "404", "error": "not_found"})
        if request.method == "GET":
            return httpx.Response(200, content=self.objects[key])
        if request.method == "HEAD":
            return httpx.Response(200)
        if request.method == "DELETE":
            del self.objects[key]
            return httpx.Response(200, json={"message": "Successfully deleted"})
        return httpx.Response(405)


    def listing(self, body: dict) -> list[dict]:
        """One folder level, like the real list call: folders have no id."""
        prefix, entries = body["prefix"], {}
        for full in self.objects:
            key = full.removeprefix(f"{BUCKET}/")
            if prefix and not key.startswith(prefix + "/"):
                continue
            rest = key[len(prefix) + 1:] if prefix else key
            name = rest.split("/")[0]
            entries[name] = {"name": name, "id": None if "/" in rest else "id-" + name}
        page = sorted(entries.values(), key=lambda e: e["name"])
        return page[body["offset"]:body["offset"] + body["limit"]]


@pytest.fixture
def api():
    return FakeStorageApi()


@pytest.fixture
def store(api):
    return SupabaseStorage(URL + "/", KEY, BUCKET, client=httpx.Client(transport=httpx.MockTransport(api)))


def test_supabase_round_trip(store, api):
    store.prepare()
    store.prepare()  # the second start finds the bucket and carries on
    key = "cv/2026/0d9c…/السيرة الذاتية.pdf"
    store.save(key, b"%PDF-1.7 data")
    assert store.exists(key) and store.read(key) == b"%PDF-1.7 data"
    assert any(r.url.path.startswith(f"/storage/v1/object/authenticated/{BUCKET}/cv/2026/") for r in api.seen)
    store.delete(key)
    assert not store.exists(key)
    store.delete(key)  # deleting twice is not an error (the purge job may retry)
    with pytest.raises(FileNotFoundError):
        store.read(key)


def test_supabase_errors_are_raised(api):
    def broken(request):
        return httpx.Response(500, json={"error": "internal"})
    s = SupabaseStorage(URL, KEY, BUCKET, client=httpx.Client(transport=httpx.MockTransport(broken)))
    with pytest.raises(httpx.HTTPStatusError):
        s.save("x", b"1")
    with pytest.raises(httpx.HTTPStatusError):
        s.exists("x")
    with pytest.raises(RuntimeError):
        SupabaseStorage("", "", BUCKET)


def test_backend_comes_from_the_configuration(monkeypatch, tmp_path):
    monkeypatch.setenv("STORAGE_BACKEND", "local")
    monkeypatch.setenv("LOCAL_STORAGE_DIR", str(tmp_path / "files"))
    get_settings.cache_clear()
    try:
        local = files.storage()
        assert isinstance(local, files.LocalStorage)
        local.prepare()
        assert (tmp_path / "files").is_dir()
        monkeypatch.setenv("STORAGE_BACKEND", "supabase")
        monkeypatch.setenv("SUPABASE_URL", URL)
        monkeypatch.setenv("SUPABASE_SERVICE_KEY", KEY)
        get_settings.cache_clear()
        files._supabase.cache_clear()
        remote = files.storage()
        assert isinstance(remote, SupabaseStorage) and remote.bucket == BUCKET and files.storage() is remote
    finally:
        get_settings.cache_clear()
        files._supabase.cache_clear()


def test_bucket_copy_for_the_nightly_backup(store, tmp_path):
    spec = importlib.util.spec_from_file_location("backup_files",
                                                  Path(__file__).resolve().parents[1] / "scripts" / "backup_files.py")
    backup_files = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(backup_files)
    files_in = {"cv/2026/a": b"cv a", "cv/2026/b": b"cv b", "report_attachment/2026/c": b"report c", "top": b"t"}
    for key, data in files_in.items():
        store.save(key, data)
    assert sorted(store.keys()) == sorted(files_in)
    assert backup_files.backup(store, tmp_path / "files.tar") == 4
    with tarfile.open(tmp_path / "files.tar") as tar:
        assert {m.name: tar.extractfile(m).read() for m in tar.getmembers()} == files_in
    for key in files_in:
        store.delete(key)
    assert store.keys() == []
    assert backup_files.restore(store, tmp_path / "files.tar") == 4
    assert {key: store.read(key) for key in files_in} == files_in
