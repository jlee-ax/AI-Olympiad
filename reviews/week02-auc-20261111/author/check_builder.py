from pathlib import Path
import contextlib, hashlib, importlib.util, io, json, os, subprocess, sys, tempfile
import nbformat
repo=Path.cwd();root=repo/'reviews/week02-auc-20261111/author';builder=repo/'lessons/week02/build_week02.py';source=repo/'lessons/week02/week02_prediction_evaluation.ipynb'
python=sys.executable; before=hashlib.sha256(source.read_bytes()).hexdigest(); results={}
with tempfile.TemporaryDirectory(prefix='builder-check-',dir=root) as temp:
 d=Path(temp)
 def run(*args):
  r=subprocess.run([python,'-B',str(builder),*map(str,args)],capture_output=True,text=True)
  return {'code':r.returncode,'stdout':r.stdout[-500:],'stderr':r.stderr[-500:]}
 a=d/'generated-a.ipynb';b=d/'generated-b.ipynb'
 results['new_a']=run('--output',a,'--check-source',source)
 results['new_b']=run('--output',b)
 assert results['new_a']['code']==results['new_b']['code']==0
 assert a.read_bytes()==b.read_bytes()
 results['deterministic_sha256']=hashlib.sha256(a.read_bytes()).hexdigest()
 built=nbformat.read(a,as_version=4);lesson=nbformat.read(source,as_version=4)
 project=lambda book:[(c.id,c.cell_type,c.source) for c in book.cells]
 assert project(built)==project(lesson)
 results['projection_equal']=True
 sentinel=d/'sentinel.ipynb';sentinel.write_text('keep',encoding='utf-8')
 directory=d/'already.ipynb';directory.mkdir()
 dangling=d/'dangling.ipynb';dangling.symlink_to(d/'missing.ipynb')
 linked=d/'linked-parent';linked.symlink_to(d,target_is_directory=True)
 for name,target in [('existing_file',sentinel),('existing_dir',directory),('dangling_symlink',dangling),('symlink_parent',linked/'new.ipynb'),('missing_parent',d/'missing'/'new.ipynb')]:
  results[name]=run('--output',target);assert results[name]['code']!=0,name
 assert sentinel.read_text()=='keep' and not (d/'new.ipynb').exists()
 results['no_args']=run();assert results['no_args']['code']!=0
 # An import must not parse unrelated argv, exit, write a file, or change the source.
 before_files=set(d.iterdir()); saved_argv=sys.argv[:]; sys.argv=['build_week02.py','--unrelated-test-argument']
 try:
  spec=importlib.util.spec_from_file_location('week02_builder_import_test',builder)
  module=importlib.util.module_from_spec(spec)
  captured=io.StringIO()
  with contextlib.redirect_stdout(captured), contextlib.redirect_stderr(captured):spec.loader.exec_module(module)
 finally:sys.argv=saved_argv
 assert callable(module.main) and captured.getvalue()=='' and set(d.iterdir())==before_files
 assert hashlib.sha256(source.read_bytes()).hexdigest()==before
 results['import_safe']=True
 # Fault injection: fail after writing bytes to a newly exclusive-created destination.
 partial=d/'partial.ipynb';original_open=Path.open
 class FaultWriter:
  def __init__(self,wrapped):self.wrapped=wrapped
  def __enter__(self):return self
  def __exit__(self,*args):self.wrapped.close();return False
  def fileno(self):return self.wrapped.fileno()
  def write(self,text):
   self.wrapped.write(text[:25]);self.wrapped.flush();raise OSError('injected write failure')
 def injected_open(path,mode='r',*args,**kwargs):
  wrapped=original_open(path,mode,*args,**kwargs)
  return FaultWriter(wrapped) if path==partial and mode=='x' else wrapped
 Path.open=injected_open
 try:
  try:module.main(['--output',str(partial)])
  except OSError as exc:assert 'injected write failure' in str(exc)
  else:raise AssertionError('injected failure was not raised')
 finally:Path.open=original_open
 assert not partial.exists() and sentinel.read_text()=='keep'
 results['partial_write_cleanup']=True
 altered=d/'altered.ipynb';lesson.cells[0].source+='\n변경';nbformat.write(lesson,altered)
 results['mismatched_source']=run('--check-source',altered);assert results['mismatched_source']['code']!=0
 assert hashlib.sha256(source.read_bytes()).hexdigest()==before
results['source_sha256_unchanged']=before
out=root/'builder-checks.json'
with out.open('x',encoding='utf-8') as f:json.dump(results,f,indent=2,ensure_ascii=False)
print(json.dumps({'source_sha256':before,'generated_sha256':results['deterministic_sha256'],'projection_equal':True,'refusals':['existing file','existing directory','dangling symlink','symlink parent','missing parent','no arguments','source mismatch'],'import_safe':True,'partial_write_cleanup':True},ensure_ascii=False))
