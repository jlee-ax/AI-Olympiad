import ast,hashlib,json,re
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
D=Path(__file__).resolve().parent;R=D.parents[2]
digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
manifest=json.loads((D/'final-input-manifest.json').read_text());assert all(digest(R/x['path'])==x['sha256']==digest(D/x['snapshot']) for x in manifest['inputs'])
book=json.loads((D/'final-inputs/week01_integrated.ipynb').read_text());baseline=json.loads((D/'baseline-manifest.json').read_text())
original=next(x for x in baseline['inputs'] if x['path'].endswith('week01_python_tables.ipynb'));bridge=next(x for x in baseline['inputs'] if x['path'].endswith('week01_axes_linear_bridge.ipynb'));plan=next(x for x in baseline['inputs'] if x['path'].endswith('student-plan.html'))
assert original['cell_count']==89
unchanged=[]
for x in [original,bridge,plan]:assert digest(R/x['path'])==x['sha256'];unchanged.append({'path':x['path'],'sha256':x['sha256'],'unchanged':True})
old=next(x for x in baseline['inputs'] if x['path'].endswith('week01_integrated.ipynb'));oldcode=[2,4,6,8,10,12,14,16,18,20,22,24,26,28,30,32,34,36];code_hashes=[digest_source:=hashlib.sha256(''.join(c['source']).encode()).hexdigest() for c in book['cells'] if c['cell_type']=='code'];assert all(old['cell_source_sha256'][i] in code_hashes for i in oldcode)
blanks=[]
for i in [38,42]:assert not ast.parse(''.join(book['cells'][i]['source'])).body;blanks.append(i)
class AuditHTML(HTMLParser):
 def __init__(self):super().__init__();self.stack=[];self.common=[];self.parts=[]
 def handle_starttag(self,tag,attrs):
  if tag not in {'meta','link','img','input','br','hr','source','wbr'}:self.stack.append(tag)
 def handle_endtag(self,tag):
  if tag in self.stack:
   pos=len(self.stack)-1-self.stack[::-1].index(tag);self.stack=self.stack[:pos]
 def handle_data(self,data):
  if 'script' not in self.stack and 'style' not in self.stack:self.parts.append(data)
  if '계산과 이유, 직접 작성한 코드' in data:self.common.append({'line':self.getpos()[0],'ancestors':list(self.stack),'text':data.strip()})
def html_audit(folder):
 p=D/folder/'week01_integrated.html';h=AuditHTML();h.feed(p.read_text());return h
before=html_audit('candidate-387b-inputs');after=html_audit('final-inputs');assert before.common and after.common
assert any('li' in x['ancestors'] for x in before.common)
assert all('li' not in x['ancestors'] and 'ol' not in x['ancestors'] for x in after.common)
text=''.join(after.parts);assert '**잘라낸 부분(crop)**' not in text
assert '3,136' in text and '0.0625' in text and '원본' in text
assert 6.25/100==0.0625==1/16 and 224*224==50176 and 224*224//16==3136
patterns=[]
for i,c in enumerate(book['cells']):
 if c['cell_type']=='markdown':
  for m in re.finditer(r'\d+\s*(?:분|시간)|자습|실측|검증 완료|검증 성공',''.join(c['source'])):patterns.append({'cell':i,'match':m.group()})
teacher=(D/'final-inputs/week01_integrated_teacher.md').read_text();assert '89셀' in teacher and '91셀' in teacher and '같은 셀 번호라고 단정하지 않습니다' in teacher
out={'final_input_hashes_current':True,'unchanged_original_bridge_plan':unchanged,'all18_old_integrated_code_sources_preserved':True,'blank_student_cells':blanks,'original_numbering_verified_for_safe89_only':True,'protected_user91_not_read_or_executed':True,'HTML_common_instruction_initial_387b':before.common,'HTML_common_instruction_final':after.common,'HTML_common_paragraph_outside_list':True,'old_asterisk_rendering_fixed':True,'percentage_and_official_area_arithmetic_correct':True,'student_internal_time_status_pattern_hits':patterns,'HTML_scope':'source parsing only; browser visual rendering not observed','generic_student_rectangle_function':'absent; blank42 requires learner implementation','RGB_scope':'spatial-pixel arithmetic explained; only 2D implementation required','burden':'one duplicated prompt consolidated, but required underlying function/hand calculations/error checks remain; actual total work/time not measured'}
(D/'content-audit-results.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'hashes_ok':True,'HTML_common_paragraph_outside_list':True,'blank_cells':blanks,'old_code_preserved':True,'internal_time_hits':patterns},ensure_ascii=False))
