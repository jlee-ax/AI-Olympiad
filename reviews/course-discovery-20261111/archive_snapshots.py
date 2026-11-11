"""Deterministically archive only duplicate session-NN snapshots; retain final files.
Creation verifies archived bytes against every original SHA before unlinking those
explicitly enumerated intermediate snapshots. Events, failures, current/final sessions,
reports, manifests, projections, source notes and scripts remain expanded.
"""
import argparse,gzip,hashlib,io,json,tarfile
from pathlib import Path
BASE=Path(__file__).resolve().parent
ARCHIVE=BASE/'state-snapshots.tar.gz'
MANIFEST=BASE/'snapshot-archive-manifest.json'
def digest(data):return hashlib.sha256(data).hexdigest()
def verify(expected):
 with tarfile.open(ARCHIVE,'r:gz') as archive:
  members=archive.getmembers()
  if sorted(m.name for m in members)!=sorted(x['path'] for x in expected):raise ValueError('Archive member set differs')
  observed=[]
  for item in expected:
   m=archive.getmember(item['path'])
   if not m.isfile():raise ValueError('Unexpected non-file member')
   b=archive.extractfile(m).read()
   if digest(b)!=item['sha256'] or len(b)!=item['bytes']:raise ValueError('Archived bytes differ: '+item['path'])
   observed.append(item['path'])
 return observed
ap=argparse.ArgumentParser();ap.add_argument('operation',choices=['create','verify']);ap.add_argument('--tag',choices=['bridge','bridge-final','cli-reports','cli-reports-final']);a=ap.parse_args()
if a.tag:
 ARCHIVE=BASE/('state-snapshots-'+a.tag+'.tar.gz');MANIFEST=BASE/('snapshot-archive-manifest-'+a.tag+'.json')
if a.tag=='cli-reports':
 ARCHIVE=BASE/'cli-report-replays.tar.gz';MANIFEST=BASE/'cli-report-archive-manifest.json'
if a.tag=='cli-reports-final':
 ARCHIVE=BASE/'cli-report-replays-final.tar.gz';MANIFEST=BASE/'cli-report-archive-manifest-final.json'
if a.operation=='create':
 if ARCHIVE.exists() or MANIFEST.exists():raise ValueError('Archive already exists; verify rather than replace it')
 paths=sorted(BASE.glob('checks/final-*/*-report.json' if a.tag in ['cli-reports','cli-reports-final'] else 'runs/*/session-[0-9][0-9].json'))
 if not paths:raise ValueError('No intermediate snapshots')
 entries=[{'path':str(p.relative_to(BASE)),'bytes':p.stat().st_size,'sha256':digest(p.read_bytes())} for p in paths]
 with ARCHIVE.open('wb') as raw:
  with gzip.GzipFile(filename='',mode='wb',compresslevel=9,fileobj=raw,mtime=0) as zipped:
   with tarfile.open(fileobj=zipped,mode='w',format=tarfile.USTAR_FORMAT) as tar:
    for p,item in zip(paths,entries):
     data=p.read_bytes()
     if digest(data)!=item['sha256']:raise ValueError('Snapshot changed during archive creation')
     m=tarfile.TarInfo(item['path']);m.size=len(data);m.mtime=0;m.mode=0o644;m.uid=0;m.gid=0;m.uname='';m.gname='';tar.addfile(m,io.BytesIO(data))
 verified=verify(entries)
 manifest={'archive':ARCHIVE.name,'archive_sha256':digest(ARCHIVE.read_bytes()),'archive_bytes':ARCHIVE.stat().st_size,'original_bytes':sum(x['bytes'] for x in entries),'file_count':len(entries),'method':'Python tarfile USTAR in sorted relative path order; mode0644 uid/gid0 empty owner names mtime0; gzip level9 filename empty mtime0. Exact original bytes; no JSON reserialization.','verification':'Read every member back from finished archive and check path, regular-file type, byte length and SHA-256 against originals before unlinking only these explicitly listed duplicate expanded files.','expanded_files_retained':'session.json, report.json, manifest.json, all event files, failure records, input projections/source notes, command evidence and scripts.','files':entries,'verified_member_count':len(verified),'deletion_scope':('Only the explicitly listed checks/final-*/*-report.json duplicate CLI replay receipts; authoritative runs/*/report.json and current-summary files stay expanded.' if a.tag in ['cli-reports','cli-reports-final'] else 'Only the explicitly listed runs/*/session-NN.json duplicate snapshots, per parent instruction. Historical bytes are retained in the verified archive.')}
 MANIFEST.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
 for p,item in zip(paths,entries):
  if digest(p.read_bytes())!=item['sha256']:raise ValueError('Original changed before unlink; stop')
  p.unlink()
else:
 manifest=json.loads(MANIFEST.read_text())
 if digest(ARCHIVE.read_bytes())!=manifest['archive_sha256']:raise ValueError('Archive SHA differs')
 verified=verify(manifest['files'])
print(json.dumps({'archive':str(ARCHIVE),'file_count':len(verified),'verified':True,'archive_sha256':digest(ARCHIVE.read_bytes()),'archive_bytes':ARCHIVE.stat().st_size},ensure_ascii=False,indent=2))
