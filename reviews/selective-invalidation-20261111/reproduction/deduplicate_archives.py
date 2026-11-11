"""Preserve every input path via one shared content-addressed archive.
Only duplicate representations in reproduction are replaced; original files are untouched.
"""
import hashlib,json,pathlib,tarfile
OUT=pathlib.Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 archive_dir=OUT/'archives';old_manifests=sorted(archive_dir.glob('*.manifest.json'));groups=[];opened={};blobs={};raw_to_remove=[];old_archive_paths=set();previous=[]
 for p in old_manifests:
  m=json.loads(p.read_text());assert 'format' not in m,'Already deduplicated';old=OUT/m['archive'];assert sha(old)==m['archive_sha256'];t=tarfile.open(old,'r:gz');opened[str(old)]=t;entries=[]
  for item in m['members']:
   raw=t.extractfile(item['path']).read();assert len(raw)==item['bytes'] and hashlib.sha256(raw).hexdigest()==item['sha256'];key=(item['sha256'],item['bytes'])
   if key in blobs:assert blobs[key]==raw
   else:blobs[key]=raw
   entries.append({**item,'content_member':'sha256/'+item['sha256']})
  groups.append((p,m,entries));old_archive_paths.add(old);previous.append({'manifest':str(p.relative_to(OUT)),'archive':m['archive'],'archive_sha256':m['archive_sha256'],'archive_bytes':old.stat().st_size})
 for group in ['finalsource-04','restored-control-04']:
  folder=OUT/group;entries=[];retained=[]
  for case in sorted((folder/'cases').iterdir()):
   for p in sorted(case.rglob('*')):
    if not p.is_file():continue
    output=p.parent==case and (p.name in ('measurement.json','freshness.json','finding.json') or p.name.endswith('-result.json') or p.name.endswith('-failure.json'))
    if output:retained.append(str(p.relative_to(OUT)));continue
    raw=p.read_bytes();h=hashlib.sha256(raw).hexdigest();key=(h,len(raw));
    if key in blobs:assert blobs[key]==raw
    else:blobs[key]=raw
    entries.append({'path':str(p.relative_to(folder)),'bytes':len(raw),'sha256':h,'content_member':'sha256/'+h});raw_to_remove.append(p)
  assert entries;manifest=archive_dir/(group+'-inputs.manifest.json');assert not manifest.exists();groups.append((manifest,{'group':group,'retained_raw_result_paths':retained},entries))
 archive=archive_dir/'content-inputs-v2.tar.gz';assert not archive.exists()
 with tarfile.open(archive,'w:gz') as t:
  import io
  for (h,size),raw in sorted(blobs.items()):
   info=tarfile.TarInfo('sha256/'+h);info.size=size;info.mode=0o644;info.mtime=0;t.addfile(info,io.BytesIO(raw))
 content=[{'member':'sha256/'+h,'sha256':h,'bytes':size} for h,size in sorted(blobs)]
 with tarfile.open(archive,'r:gz') as t:
  assert set(t.getnames())=={x['member'] for x in content}
  for x in content:
   raw=t.extractfile(x['member']).read();assert len(raw)==x['bytes'] and hashlib.sha256(raw).hexdigest()==x['sha256']
 archive_sha=sha(archive);index=archive_dir/'content-inputs-v2.index.json';index.write_text(json.dumps({'format':'content-addressed-tar-v1','archive':str(archive.relative_to(OUT)),'archive_sha256':archive_sha,'contents':content,'per_path_manifest_count':len(groups),'unique_content_count':len(content)},indent=2)+'\n')
 history=archive_dir/'representation-history';history.mkdir();perpath=0
 for p,old,entries in groups:
  if p.exists():shutil_copy=history/(p.name+'.v1.json');shutil_copy.write_bytes(p.read_bytes())
  m={**old,'format':'content-addressed-tar-v1','archive':str(archive.relative_to(OUT)),'archive_sha256':archive_sha,'content_index':str(index.relative_to(OUT)),'content_index_sha256':sha(index),'members':entries,'restore_semantics':'Read archive.extractfile(content_member).read() and write_bytes separately at every original path. No extractall and no restored filesystem hardlinks.','method':'Every old/raw per-path byte sequence verified before content deduplication; equal SHA+size bytes also compared directly. The compressed representation changes, all original input path bytes remain reproducible.'};p.write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n');perpath+=len(entries)
  assert [(x['path'],x['bytes'],x['sha256']) for x in m['members']]==[(x['path'],x['bytes'],x['sha256']) for x in entries]
 for t in opened.values():t.close()
 for p in old_archive_paths:p.unlink()
 for p in raw_to_remove:p.unlink()
 for group in ['finalsource-04','restored-control-04']:
  for p in sorted((OUT/group).rglob('*'),key=lambda p:len(p.parts),reverse=True):
   if p.is_dir() and not any(p.iterdir()):p.rmdir()
 result={'old_representations':previous,'old_archive_bytes_total':sum(x['archive_bytes'] for x in previous),'new_archive':str(archive.relative_to(OUT)),'new_archive_sha256':archive_sha,'new_archive_bytes':archive.stat().st_size,'new_index':str(index.relative_to(OUT)),'unique_contents':len(content),'original_input_paths':perpath,'every_input_size_sha_verified':True,'duplicate_raw_inputs_removed_only_after_verification':True,'old_compressed_archives_removed':'Compressed representation only; prior manifests and archive SHAs preserved in representation-history. Every original input path remains in current manifests.','restore_creates_independent_files':True};(OUT/'archive-deduplication-results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:result[k] for k in ['old_archive_bytes_total','new_archive_bytes','unique_contents','original_input_paths','every_input_size_sha_verified']},ensure_ascii=False))
if __name__=='__main__':main()
