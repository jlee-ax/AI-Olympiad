"""Restore CAS evidence as independent files; never extract hardlinks or read symlink targets."""
from pathlib import Path
import argparse,hashlib,json,os,stat,tarfile
OUT=Path(__file__).resolve().parent

def restore(archive,destination):
    destination=Path(destination).resolve()
    if not destination.is_relative_to(OUT):raise ValueError('Destination must remain in this independent directory')
    destination.mkdir(parents=True,exist_ok=False)
    with tarfile.open(archive,'r:gz') as tar:
        manifest=json.loads(tar.extractfile('manifest.json').read())
        for entry in manifest['entries']:
            relative=Path(entry['path']);target=destination/relative
            if relative.is_absolute() or '..' in relative.parts:raise ValueError('Unsafe archived path')
            target.parent.mkdir(parents=True,exist_ok=True)
            if entry['kind']=='directory':target.mkdir(exist_ok=True)
            elif entry['kind']=='symlink':os.symlink(entry['link_target'],target)
            else:
                data=tar.extractfile('blobs/'+entry['sha256']).read()
                assert len(data)==entry['size'] and hashlib.sha256(data).hexdigest()==entry['sha256']
                target.write_bytes(data)  # Independent write for EVERY path, including duplicate content.
                os.chmod(target,entry['mode'])
        for entry in manifest['entries']:
            target=destination/entry['path']
            if entry['kind']=='directory':os.chmod(target,entry['mode'])
            elif entry['kind']=='symlink':assert os.readlink(target)==entry['link_target']
            else:assert hashlib.sha256(target.read_bytes()).hexdigest()==entry['sha256']
    return manifest
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--archive',type=Path,default=OUT/'evidence-cas.tar.gz');p.add_argument('--destination',type=Path,required=True);a=p.parse_args()
    m=restore(a.archive,a.destination);print(json.dumps({'restored_entries':len(m['entries']),'independent_regular_file_writes':sum(e['kind']=='regular' for e in m['entries']),'symlink_targets_not_read':True}))
