_CASE='valid-edge-equality'
_IMPLEMENTATION='reviewer'
_MUTATION='reject-valid-stop'
from pathlib import Path
exec((Path.cwd().parents[1]/'rectangle_case_oracle.py').read_text())
