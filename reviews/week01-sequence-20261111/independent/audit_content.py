import ast,hashlib,json,re
from pathlib import Path
from html.parser import HTMLParser
D=Path(__file__).resolve().parent;R=D.parents[2]
class Text(HTMLParser):
 def __init__(self):super().__init__();self.parts=[]
 def handle_data(self,s):self.parts.append(s)
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
final=json.loads((D/'final-input-manifest.json').read_text());rows=[]
for x in final['inputs']:
 p=R/x['path'];assert digest(p)==x['sha256'];rows.append({**x,'unchanged':True})
B=json.loads((R/'lessons/week01/week01_axes_linear_bridge.ipynb').read_text());I=json.loads((R/'lessons/week01/week01_integrated.ipynb').read_text())
blank=[]
for name,book,indices in [('bridge',B,[29,33]),('integrated',I,[36])]:
 for k in indices:
  v=not ast.parse(''.join(book['cells'][k]['source'])).body;assert v;blank.append({'notebook':name,'cell':k,'ast_empty':v})
old=json.loads((D/'runs/full-bridge/result.json').read_text());allcode=True;stored=True
for c in old['cells']:
 cell=B['cells'][c['index']];allcode &= hashlib.sha256(''.join(cell['source']).encode()).hexdigest()==c['source_sha']
 # Compare text/type projection from initial actual run with current stored output.
 def proj(outputs):
  return [[o['output_type'],o.get('name'),o.get('text'),o.get('data',{}).get('text/plain'),sorted(o.get('data',{}))] for o in outputs]
 stored &= proj(c['outputs'])==proj(cell.get('outputs',[]))
assert allcode and stored
html=[]
for name,markers in [('week01_axes_linear_bridge',['코드 읽기:','lookup_and_masked_mean','실제 토큰 ID 5','유효 위치 평균']),('week01_integrated',['def lookup_and_masked_mean(table, token_ids):','입력 코드 셀을 실행한 뒤 빈 답안 셀에 직접 작성','과제 D·E'])]:
 h=Text();h.feed((R/'lessons/week01'/f'{name}.html').read_text());text=''.join(h.parts);matches={m:m in text for m in markers};assert all(matches.values());html.append({'file':name+'.html','key_updated_content_present':matches,'scope':'HTML source parsed, visual rendering unobserved'})
patterns=[]
for name,book in [('bridge',B),('integrated',I)]:
 for k,c in enumerate(book['cells']):
  if c['cell_type']=='markdown':
   for match in re.finditer(r'\d+\s*(?:분|시간)|자습|실측|검증 완료|검증 성공', ''.join(c['source'])):patterns.append({'notebook':name,'cell':k,'match':match.group()})
# Known source/plan locations and unchanged baseline material.
baseline=json.loads((D/'baseline-manifest.json').read_text());unchanged=[]
for x in baseline['inputs']:
 if 'axes_linear_bridge' not in x['path'] and 'integrated' not in x['path']:
  p=R/x['path'];unchanged.append({'path':x['path'],'frozen_sha':x['sha256'],'current_sha':digest(p),'unchanged':digest(p)==x['sha256']})
assert all(x['unchanged'] for x in unchanged)
out={'final_input_hashes':rows,'blank_student_responses':blank,'bridge_all_code_and_stored_text_unchanged_since_initial_candidate':allcode and stored,'integrated_source_changed_vs_frozen_baseline':[37],'html':html,'student_internal_time_status_pattern_hits':patterns,'untouched_baseline_inputs':unchanged,'classification':'Course instructions to solve, execute Jupyter, use a new kernel, save own answer and record help remain educational instructions, not internal schedule/status.','student_time_and_achievement':'unobserved','visual_browser':'not tested; no policy bypass'}
(D/'content-audit-results.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'blank_cells':len(blank),'html_documents':len(html),'time_pattern_hits':patterns,'unchanged_inputs':len(unchanged)},ensure_ascii=False))
