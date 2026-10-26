"""Copy every uploaded file of the Supabase bucket into one tar archive, or put an archive back (NFR-REL-02; the
copy is run by .github/workflows/backup.yml, which encrypts it). From backend/:

    SUPABASE_URL=... SUPABASE_SERVICE_KEY=... python scripts/backup_files.py files.tar
    SUPABASE_URL=... SUPABASE_SERVICE_KEY=... python scripts/backup_files.py --restore files.tar

Each file is stored under its storage key, so a restore puts it back where the database expects it."""
import io
import os
import sys
import tarfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.storage_supabase import SupabaseStorage  # noqa: E402


def backup(store: SupabaseStorage, out: Path) -> int:
    keys = store.keys()
    with tarfile.open(out, "w") as tar:
        for key in keys:
            data = store.read(key)
            info = tarfile.TarInfo(key)
            info.size = len(data)
            tar.addfile(info, io.BytesIO(data))
    return len(keys)


def restore(store: SupabaseStorage, archive: Path) -> int:
    store.prepare()
    n = 0
    with tarfile.open(archive) as tar:
        for member in tar.getmembers():
            if member.isfile():
                store.save(member.name, tar.extractfile(member).read())
                n += 1
    return n


def main(argv: list[str]) -> int:
    args = [a for a in argv if a != "--restore"]
    if len(args) != 1:
        print(__doc__, file=sys.stderr)
        return 2
    store = SupabaseStorage(os.environ.get("SUPABASE_URL", ""), os.environ.get("SUPABASE_SERVICE_KEY", ""),
                            os.environ.get("STORAGE_BUCKET", "internsync-files"))
    if "--restore" in argv:
        print(f"{restore(store, Path(args[0]))} files restored")
    else:
        print(f"{backup(store, Path(args[0]))} files copied")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
