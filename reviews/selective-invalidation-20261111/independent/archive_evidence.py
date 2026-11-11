"""Exact-byte evidence packaging only. Does not edit repository source or original records."""
from pathlib import Path
import gzip,hashlib,io,json,os,shutil,stat,subprocess,sys,tarfile
from datetime import datetime,timezone
from restore_evidence import restore
OUT=Path(__file__).resolve().parent;REPO=OUT.parents[2]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
entries=[];blobs={};logical_bytes=0
for tree in ['inputs','cases']:
    parent=OUT/tree
    for path in sorted([parent,*parent.rglob('*')]):
        info=path.lstat();entry={'path':str(path.relative_to(OUT)),'mode':stat.S_IMODE(info.st_mode)}
        if stat.S_ISLNK(info.st_mode):
            target=os.readlink(path);entry.update(kind='symlink',link_target=target,link_target_sha256=hashlib.sha256(os.fsencode(target)).hexdigest());entries.append(entry);continue
        if stat.S_ISDIR(info.st_mode):entry.update(kind='directory');entries.append(entry);continue
        if not stat.S_ISREG(info.st_mode):raise ValueError('Unexpected evidence filesystem object '+str(path))
        data=path.read_bytes();digest=hashlib.sha256(data).hexdigest();entry.update(kind='regular',sha256=digest,size=len(data));entries.append(entry);blobs.setdefault(digest,data);logical_bytes+=len(data)
manifest={'format':'content-addressed-tar-v1','scope':'Only newly created independent inputs/ and cases/ copies. Original repository/source/reviews are excluded.','entries':entries,'logical_regular_bytes':logical_bytes,'unique_blobs':len(blobs),'unique_blob_bytes':sum(map(len,blobs.values())),'restore_rule':'Read blob bytes from archive and write_bytes once per path; never recreate hardlinks. Preserve original symlink target metadata without following the links.'}
manifest_bytes=(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n').encode();(OUT/'evidence-archive-manifest.json').write_bytes(manifest_bytes)
archive=OUT/'evidence-cas.tar.gz';assert not archive.exists()
with archive.open('wb') as target:
    with gzip.GzipFile(fileobj=target,mode='wb',mtime=0) as gz:
        with tarfile.open(fileobj=gz,mode='w') as tar:
            for name,data in [('manifest.json',manifest_bytes),*[(('blobs/'+k),v) for k,v in sorted(blobs.items())]]:
                item=tarfile.TarInfo(name);item.size=len(data);item.mode=0o644;item.mtime=0;tar.addfile(item,io.BytesIO(data))
verification=OUT/'archive-restore-verification';restored=restore(archive,verification)
assert restored==manifest
regular=[e for e in entries if e['kind']=='regular'];identities=[]
for entry in entries:
    old=OUT/entry['path'];new=verification/entry['path']
    if entry['kind']=='regular':
        assert old.read_bytes()==new.read_bytes() and sha(new)==entry['sha256'];identities.append((new.stat().st_dev,new.stat().st_ino))
    elif entry['kind']=='symlink':assert os.readlink(old)==os.readlink(new)==entry['link_target']
assert len(set(identities))==len(identities),'Restored duplicate content must not share hardlink inodes'
byhash={}
for entry in regular:byhash.setdefault(entry['sha256'],[]).append(entry)
pair=next(values[:2] for values in byhash.values() if len(values)>1)
first,second=[verification/e['path'] for e in pair];original=first.read_bytes();first.write_bytes(original+b' independent-file probe');assert sha(second)==pair[1]['sha256'];first.write_bytes(original)
# Functional reconstruction test at a relocated root, using restored frozen tool bytes.
command=[sys.executable,'-B',str(verification/'inputs/v4-tools/quality.py'),'evaluate',str(verification/'cases/v4-control/bundle.json'),'--root',str(verification/'cases/v4-control/root')]
proc=subprocess.run(command,capture_output=True,text=True,timeout=60);value=json.loads(proc.stdout);expected=json.loads((verification/'cases/v4-control/evaluate.json').read_text());assert proc.returncode==0 and value==expected and value['ready_for_review']
# Validate originals once more before removing only the duplicate evidence trees.
for entry in entries:
    path=OUT/entry['path']
    if entry['kind']=='regular':assert sha(path)==entry['sha256'] and path.stat().st_size==entry['size']
    elif entry['kind']=='symlink':assert os.readlink(path)==entry['link_target']
record={'verified_at_utc':datetime.now(timezone.utc).isoformat(),'archive':'evidence-cas.tar.gz','archive_sha256':sha(archive),'archive_bytes':archive.stat().st_size,'manifest':'evidence-archive-manifest.json','manifest_sha256':sha(OUT/'evidence-archive-manifest.json'),'regular_paths':len(regular),'symlink_paths':sum(e['kind']=='symlink' for e in entries),'unique_blobs':len(blobs),'logical_regular_bytes':logical_bytes,'unique_blob_bytes':manifest['unique_blob_bytes'],'all_per_path_bytes_and_hashes_verified':True,'all_restored_regular_inodes_independent':True,'duplicate_file_mutation_does_not_propagate':True,'symlink_metadata_preserved_targets_not_read':True,'restored_v4_control_cli_exact_report_equal':True,'restored_v4_control_cli_exit':proc.returncode,'duplicate_copy_trees_removed':['inputs','cases'],'original_repository_files_modified':False,'raw_summaries_and_failures_remain_outside_archive':True}
for name in ['inputs','cases']:shutil.rmtree(OUT/name)
shutil.rmtree(verification)
(OUT/'archive-verification.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n');print(json.dumps(record,ensure_ascii=False,indent=2))
