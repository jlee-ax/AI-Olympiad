"""Verify both exact assessment bundles. Does not write to disk."""
import argparse
import hashlib
from pathlib import Path

EXPECTED = {
    "diagnostic": "33e6a6da604cda42513709da68d6d494d70ba3e06787c3e7ecc29070df513a2f",
    "final": "30e43de394006489149b3c840c85ad02b8e9d2f3dd7382e1ef15b7cb4703c8ee",
}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def digest(folder):
    files = sorted(folder.iterdir(), key=lambda path: path.name)
    if len(files) != 7 or any(not item.is_file() or item.is_symlink() for item in files):
        raise ValueError(f"expected seven regular files in {folder}")
    records = [f"{sha(item.read_bytes())}  {item.name}\n" for item in files]
    return sha("".join(records).encode("utf-8"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    root = parser.parse_args().root
    for name, expected in EXPECTED.items():
        result = digest(root / name)
        print(name, result)
        if result != expected:
            raise SystemExit(f"SHA-256 mismatch in {name}")


if __name__ == "__main__":
    main()
