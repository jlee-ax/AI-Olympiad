_review_case = 'raw-dot-contract'
from pathlib import Path
exec((Path.cwd().parents[1]/"native_probe.py").read_text(),globals())
