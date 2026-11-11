"""Lossless input-copy preservation. All pack/restore writes stay under reproduction."""
import argparse,hashlib,json,pathlib,tarfile
OUT=pathlib.Path(__file__).resolve().parent;ROOT=OUT.parents[2]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def manifests():return sorted((OUT/'archives').glob('*.manifest.json'))
def verify(p):
 m=json.loads(p.read_text());archive=OUT/m['archive'];assert sha(archive)==m['archive_sha256'];checks=[]
 with tarfile.open(archive,'r:gz') as t:
  if m.get('format')=='content-addressed-tar-v1':
   index=OUT/m['content_index'];assert sha(index)==m['content_index_sha256'];values=json.loads(index.read_text());assert values['archive_sha256']==m['archive_sha256'];assert set(t.getnames())=={x['member'] for x in values['contents']};seen={}
   for x in values['contents']:
    raw=t.extractfile(x['member']).read();seen[x['member']]=(len(raw),hashlib.sha256(raw).hexdigest());assert seen[x['member']]==(x['bytes'],x['sha256'])
   for x in m['members']:checks.append(seen[x['content_member']]==(x['bytes'],x['sha256']))
  else:
   names=[i.name for i in t.getmembers()];assert len(names)==len(set(names))==len(m['members']);assert set(names)=={x['path'] for x in m['members']}
   for x in m['members']:
    raw=t.extractfile(x['path']).read();checks.append(len(raw)==x['bytes'] and hashlib.sha256(raw).hexdigest()==x['sha256'])
 assert all(checks);return {'manifest':str(p.relative_to(ROOT)),'group':m['group'],'member_count':len(checks),'all_member_sizes_and_hashes_match':True,'uncompressed_bytes':sum(x['bytes'] for x in m['members']),'archive_bytes':archive.stat().st_size,'format':m.get('format','regular-tar-v1')}

def pack(selected=None):
 groups=[selected] if selected else ['baseline-01','candidate-01','finalcandidate-03','candidate-findings/outside-plan-table'];summaries=[]
 for group in groups:
  folder=OUT/group;casefolders=sorted((folder/'cases').iterdir()) if (folder/'cases').is_dir() else [folder];files=[];retained=[]
  for case in casefolders:
   for p in sorted(case.rglob('*')):
    if not p.is_file():continue
    if p.parent==case and p.name in ('measurement.json','freshness.json','finding.json'):retained.append(str(p.relative_to(ROOT)));continue
    p.resolve().relative_to(OUT);files.append(p)
  if not files:raise ValueError('No raw input copies to preserve: '+group)
  name=group.replace('/','--');archive=OUT/'archives'/(name+'-inputs.tar.gz');manifest=archive.with_name(name+'-inputs.manifest.json');assert not archive.exists() and not manifest.exists();archive.parent.mkdir(exist_ok=True);members=[{'path':str(p.relative_to(folder)),'bytes':p.stat().st_size,'sha256':sha(p)} for p in files]
  with tarfile.open(archive,'w:gz') as t:
   for x,p in zip(members,files):t.add(p,arcname=x['path'],recursive=False)
  manifest.write_text(json.dumps({'group':group,'archive':str(archive.relative_to(OUT)),'archive_sha256':sha(archive),'members':members,'retained_raw_result_paths':retained,'method':'Per-file size and SHA256 verified against archive before deleting duplicate raw input copies only. Final raw results, expectations, failures and reproduction scripts are not removed.'},ensure_ascii=False,indent=2)+'\n');summary=verify(manifest)
  for p in files:p.unlink()
  for p in sorted(folder.rglob('*'),key=lambda x:len(x.parts),reverse=True):
   if p.is_dir() and not any(p.iterdir()):p.rmdir()
  summaries.append(summary)
 return summaries
def main():
 ap=argparse.ArgumentParser();ap.add_argument('command',choices=['pack','verify','restore']);ap.add_argument('--group');ap.add_argument('--destination');ap.add_argument('--prefix',default='');a=ap.parse_args()
 if a.command=='pack':result=pack(a.group)
 elif a.command=='verify':result=[verify(p) for p in manifests()]
 else:
  if not a.group or not a.destination:raise ValueError('restore needs --group and new --destination below reproduction')
  p=next(p for p in manifests() if json.loads(p.read_text())['group']==a.group);verify(p);m=json.loads(p.read_text());dest=(OUT/a.destination).resolve();dest.relative_to(OUT)
  if dest.exists():raise ValueError('Restore refuses an existing destination')
  dest.mkdir(parents=True)
  with tarfile.open(OUT/m['archive'],'r:gz') as t:
   for x in m['members']:
    if not x['path'].startswith(a.prefix):continue
    path=(dest/x['path']).resolve();path.relative_to(dest);path.parent.mkdir(parents=True,exist_ok=True);raw=t.extractfile(x.get('content_member',x['path'])).read();path.write_bytes(raw);assert len(raw)==x['bytes'] and sha(path)==x['sha256']
  result={'restored_group':a.group,'destination':str(dest.relative_to(ROOT)),'member_count':sum(x['path'].startswith(a.prefix) for x in m['members']),'prefix':a.prefix,'every_member_size_sha_verified':True}
 print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
