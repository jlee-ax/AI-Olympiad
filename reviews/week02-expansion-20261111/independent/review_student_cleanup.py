from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,re
import nbformat
from bs4 import BeautifulSoup
from nbconvert import HTMLExporter
REPO=Path('/workspace/scratch/d500e5cb2076/ai-olympiad-course-revision')
OUT=Path(__file__).resolve().parent
PATTERNS={
 'duration_allocation':r'\d+\s*(?:[~∼–-]\s*\d+)?\s*(?:분|시간)(?![가-힣])',
 'internal_timing_state':r'편성|실측|소요\s*시간|걸린\s*시간|진도\s*조정|시간\s*부족|실제\s*학생.*(?:관찰|측정)|실제\s*시간',
 'operational_context_candidate':r'수업\s*밖|필수\s*자습|교사.*(?:조정|계획)|배포\s*금지|학생.*성취.*(?:미관찰|관찰하지)',
 'learning_time_concept':r'예측\s*시점|관측\s*시각|미래|과거|시간순|윈도',
}
PATHS={
 'week01_bridge':('lessons/week01/week01_axes_linear_bridge.ipynb','reviews/week02-expansion-20261111/discovery/prechange-week01-bridge-exact.ipynb'),
 'week02_existing':('lessons/week02/week02_prediction_evaluation.ipynb','reviews/week02-expansion-20261111/discovery/prechange-week02-exact.ipynb'),
 'week01_main_observation_only':('lessons/week01/week01_python_tables.ipynb',None),
}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def matches(text):
 return {name:[{'line':i+1,'text':line.strip()} for i,line in enumerate(text.splitlines()) if re.search(pattern,line)] for name,pattern in PATTERNS.items()}
def cell_projection(html):
 soup=BeautifulSoup(html,'html.parser')
 for node in soup.select('script,style,.jp-InputPrompt,.jp-OutputPrompt'):node.decompose()
 return [re.sub(r'\s+',' ',node.get_text(' ',strip=True)).strip() for node in soup.select('.jp-Cell')]
reports={}
for name,(relative,baseline_relative) in PATHS.items():
 path=REPO/relative;before_hash=sha(path);book=nbformat.read(path,as_version=4)
 markdown='\n'.join(c.source for c in book.cells if c.cell_type=='markdown')
 full='\n'.join(c.source+'\n'+''.join(o.get('text','') for o in c.get('outputs',[])) for c in book.cells)
 html_path=path.with_suffix('.html');html=html_path.read_text()
 actual_cells=cell_projection(html)
 html_visible='\n'.join(actual_cells)
 item={'notebook':relative,'notebook_sha256':before_hash,'html_sha256':sha(html_path),'cells':len(book.cells),'notebook_candidates':matches(full),'html_candidates':matches(html_visible),'unchanged_during_read':before_hash==sha(path),'scope':'edited' if baseline_relative else 'observation_only_parent_excluded_main_week01'}
 if baseline_relative:
  before=nbformat.read(REPO/baseline_relative,as_version=4)
  before_codes=[(c.id,c.source) for c in before.cells if c.cell_type=='code']
  after_codes=[(c.id,c.source) for c in book.cells if c.cell_type=='code']
  item['code_source_and_ids_unchanged']=before_codes==after_codes
  expected_html,_=HTMLExporter().from_notebook_node(book)
  expected_cells=cell_projection(expected_html)
  item['html_cell_text_matches_fresh_export']=actual_cells==expected_cells
  item['html_cell_count']=len(actual_cells)
  item['changed_markdown_cells']=[{'index':i,'id':a.id,'before':b.source,'after':a.source} for i,(b,a) in enumerate(zip(before.cells,book.cells)) if b.source!=a.source]
  assert item['code_source_and_ids_unchanged'],name
  assert item['html_cell_text_matches_fresh_export'],name
  assert not item['notebook_candidates']['duration_allocation'],name
  assert not item['notebook_candidates']['internal_timing_state'],name
  assert not item['notebook_candidates']['operational_context_candidate'],name
  assert not item['html_candidates']['duration_allocation'],name
  assert not item['html_candidates']['internal_timing_state'],name
  assert not item['html_candidates']['operational_context_candidate'],name
 reports[name]=item
r={'checked_at_utc':datetime.now(timezone.utc).isoformat(),'files':reports,'interpretation':'Keywords are review candidates. Jupyter methods, question instructions and information-availability time concepts are not automatically internal operations. Main Week01 was explicitly excluded from changes; its heading is reported as an observation.','source_edits_by_reviewer':False,'visual_rendering':'not_performed; no browser file-URL or socket restriction bypass'}
(OUT/'student-cleanup-results.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({name:{key:item[key] for key in ('notebook_sha256','html_sha256','cells','scope','code_source_and_ids_unchanged','html_cell_text_matches_fresh_export') if key in item} for name,item in reports.items()},ensure_ascii=False,indent=2))
