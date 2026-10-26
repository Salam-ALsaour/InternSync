"""File storage on Supabase Storage for the reference deployment (Increment 2 design, Section 10).

The bucket is private and only the API holds the service key. Files are still served by `GET /files/{id}` after
the permission check of the record that owns them (NFR-SEC-04), so no bucket link ever reaches a browser."""
from urllib.parse import quote

import httpx

MISSING = (400, 404)  # Supabase answers 400 "not_found" or 404 for a missing object, depending on the version


class SupabaseStorage:
    def __init__(self, url: str, key: str, bucket: str, client: httpx.Client | None = None):
        if not url or not key:
            raise RuntimeError("STORAGE_BACKEND=supabase needs SUPABASE_URL and SUPABASE_SERVICE_KEY")
        self.base = url.rstrip("/") + "/storage/v1"
        self.bucket = bucket
        self.headers = {"Authorization": f"Bearer {key}", "apikey": key}
        self.client = client or httpx.Client(timeout=30)

    def _object(self, key: str, authenticated: bool = False) -> str:
        scope = "authenticated/" if authenticated else ""
        return f"{self.base}/object/{scope}{self.bucket}/{quote(key, safe='/')}"

    def prepare(self) -> None:
        """Create the private bucket if it does not exist yet (run by the seed at every start)."""
        r = self.client.post(f"{self.base}/bucket", headers=self.headers,
                             json={"id": self.bucket, "name": self.bucket, "public": False})
        if r.is_success or r.status_code == 409 or "already exists" in r.text.lower():
            return
        r.raise_for_status()

    def save(self, key: str, data: bytes) -> None:
        r = self.client.post(self._object(key), content=data,
                             headers={**self.headers, "Content-Type": "application/octet-stream", "x-upsert": "true"})
        r.raise_for_status()

    def read(self, key: str) -> bytes:
        r = self.client.get(self._object(key, authenticated=True), headers=self.headers)
        if r.status_code in MISSING:
            raise FileNotFoundError(key)
        r.raise_for_status()
        return r.content

    def exists(self, key: str) -> bool:
        r = self.client.head(self._object(key, authenticated=True), headers=self.headers)
        if r.status_code in MISSING:
            return False
        r.raise_for_status()
        return True

    def keys(self, prefix: str = "") -> list[str]:
        """Every object key under `prefix`, for the nightly copy of the bucket. The list call returns one folder
        level at a time; entries without an id are folders."""
        found, offset = [], 0
        while True:
            r = self.client.post(f"{self.base}/object/list/{self.bucket}", headers=self.headers,
                                 json={"prefix": prefix, "limit": 1000, "offset": offset,
                                       "sortBy": {"column": "name", "order": "asc"}})
            r.raise_for_status()
            page = r.json()
            for entry in page:
                path = f"{prefix}/{entry['name']}" if prefix else entry["name"]
                if entry.get("id") is None:
                    found += self.keys(path)
                else:
                    found.append(path)
            if len(page) < 1000:
                return found
            offset += 1000

    def delete(self, key: str) -> None:
        r = self.client.delete(self._object(key), headers=self.headers)
        if r.status_code not in MISSING:
            r.raise_for_status()
