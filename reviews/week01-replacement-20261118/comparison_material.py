"""Read the working candidate or the original immutable incumbent bytes."""
import hashlib
import re
import subprocess
from pathlib import PurePosixPath


def material(root, route, name):
    path = PurePosixPath(name)
    if path.is_absolute() or ".." in path.parts or str(path) != name:
        raise ValueError(f"Invalid route path: {name}")
    ref = route.get("basis_commit")
    if ref:
        if not re.fullmatch("[0-9a-f]{40}", ref):
            raise ValueError("Expected the full incumbent commit")
        data = subprocess.check_output(["git", "show", f"{ref}:{name}"], cwd=root)
    else:
        data = (root / name).read_bytes()
    if hashlib.sha256(data).hexdigest() != route["files"][name]:
        raise ValueError(f"Stale route input: {name}")
    return data
