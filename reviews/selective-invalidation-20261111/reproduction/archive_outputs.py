"""Compress repeated saved JSON inspection outputs after exact byte verification.
Readable expected/actual summaries, failures, reports and code remain in place.
"""
import hashlib,json,pathlib,tarfile
OUT=pathlib.Path(__file__).resolve().parent;sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 files=set()
 for group in ['baseline-01','candidate-01','finalcandidate-03','finalsource-04']:
  for case in (OUT/group/'cases').iterdir():
   for p in case.glob('*.json'):
    if p.name=='freshness.json' or (group=='baseline-01' and p.name=='measurement.json') or p.name.endswith('-result.json'):files.add(p)
 for group in ['final-cli-03','final-cli-04']:
  files.update(p for p in (OUT/group).glob('*.json') if p.name!='results.json')
 files=sorted(files);assert files;archive=OUT/'archives/inspection-outputs-v1.tar.gz';manifest=OUT/'archives/inspection-outputs-v1.manifest.json';assert not archive.exists() and not manifest.exists();members=[{'path':str(p.relative_to(OUT)),'bytes':p.stat().st_size,'sha256':sha(p)} for p in files]
 with tarfile.open(archive,'w:gz') as t:
  for p,item in zip(files,members):t.add(p,arcname=item['path'],recursive=False)
 with tarfile.open(archive,'r:gz') as t:
  assert set(t.getnames())=={x['path'] for x in members}
  for x in members:
   raw=t.extractfile(x['path']).read();assert len(raw)==x['bytes'] and hashlib.sha256(raw).hexdigest()==x['sha256']
 value={'group':'inspection-outputs','format':'regular-tar-v1','archive':str(archive.relative_to(OUT)),'archive_sha256':sha(archive),'members':members,'restore_semantics':'extractfile(member).read() then path.write_bytes; no extractall or filesystem hardlink restoration.','method':'Exact saved JSON report bytes; every size and SHA256 verified before replacing raw duplicate output files. Expected/actual summaries, versioned failures, findings and scripts remain readable.'};manifest.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
 for p in files:p.unlink()
 result={'archive':str(archive.relative_to(OUT)),'manifest':str(manifest.relative_to(OUT)),'archive_sha256':sha(archive),'output_report_count':len(files),'saved_report_bytes_before':sum(x['bytes'] for x in members),'archive_bytes_after':archive.stat().st_size,'all_original_report_sizes_and_hashes_verified':True,'readable_summary_and_failure_reports_retained':True};(OUT/'output-archive-results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result,ensure_ascii=False))
if __name__=='__main__':main()
