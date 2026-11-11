from pathlib import Path
import ast,base64,hashlib,json,subprocess
import nbformat
from nbconvert import HTMLExporter
from bs4 import BeautifulSoup
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[2]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
nb=ROOT/'lessons/week01/week01_integrated.ipynb';html=nb.with_suffix('.html');teacher=nb.with_name('week01_integrated_teacher.md')
expected={'notebook':'15ab0101edbca3c0c669e551cb723b401d168d9730523fa1ac1263a0d7538120','html':'53b48bf8370cff4f97ace9f78cbf8c5b838f7c758a56b86ef82d474003470596','teacher':'aafa8f3bbd6cc7b88131157d85a9ffa5d99d5e1b53db6abe2f021eaa2096bcdd'}
assert [sha(p) for p in [nb,html,teacher]]==list(expected.values())
book=nbformat.read(nb,as_version=4);executed=nbformat.read(OUT/'cases/candidate-15ab-main-oracles/executed.ipynb',as_version=4)
render,_=HTMLExporter().from_notebook_node(book);assert render==html.read_text()
assert not ast.parse(book.cells[32].source).body and book.cells[32].outputs==[]
source='\n'.join(c.source for c in book.cells);visible=BeautifulSoup(html.read_text(),'html.parser').get_text(' ',strip=True)
for word in ['120분','5~7시간','수업 시간','자습 시간','실측','운영 계획','편성']:
    assert word not in source and word not in visible,word
links=[]
for link in BeautifulSoup(html.read_text(),'html.parser').find_all('a',href=True):
    href=link['href']
    if not href.startswith(('https://','http://','#','mailto:','data:')):
        target=(nb.parent/href.split('#')[0]).resolve();assert target.exists(),href
        links.append(href)
plots=[]
for i,(stored,new) in enumerate(zip(book.cells,executed.cells)):
    if stored.cell_type!='code':continue
    a=[o.data['image/png'] for o in stored.outputs if o.output_type in ('display_data','execute_result') and 'image/png' in o.data]
    b=[o.data['image/png'] for o in new.outputs if o.output_type in ('display_data','execute_result') and 'image/png' in o.data]
    assert a==b,'saved/new PNG differs'
    for j,data in enumerate(a):
        path=OUT/('candidate-15ab-scatter-'+str(i)+'-'+str(j)+'.png');path.write_bytes(base64.b64decode(data));plots.append({'source_cell':i,'png':path.name,'sha256':sha(path),'saved_matches_new':True})
manifest=json.loads((OUT/'input-manifest-v1.json').read_text());preservation=[]
for row in manifest['files']:
    if row['path']=='curriculum/student-plan.html':continue
    assert sha(ROOT/row['path'])==row['sha256'],row['path']
    preservation.append({'path':row['path'],'unchanged':True,'sha256':row['sha256']})
for row in manifest['preserved_files']:
    assert sha(Path(row['path']))==row['sha256'],'protected original changed'
# No protected user content is copied; only its pre-recorded paths/hashes are checked.
old_plan=subprocess.check_output(['git','show',manifest['git_head']+':curriculum/student-plan.html'],cwd=ROOT,text=True)
current=(ROOT/'curriculum/student-plan.html').read_text();a=BeautifulSoup(old_plan,'html.parser');b=BeautifulSoup(current,'html.parser')
a1=a.select_one('#week-1');b1=b.select_one('#week-1')
assert b1.find('a',href=lambda x:x and x.endswith('/lessons/week01/week01_integrated.ipynb'))
assert '기존 추정' in b1.get_text() and '확인 전' in b1.get_text()
a1.decompose();b1.decompose();assert str(a)==str(b),'plan change outside week1'
map_rows=[
 ('Python 상태·함수·반환·오류',[5,6],'week01_python_tables.ipynb',[14,16,19,20,22,23,24,25],'followup-python','shifted_mean 새 입력, traceback 수정, 도움 기록'),
 ('CSV·자료사전·열 선택·dtype·dirty값',[1,2,3,4],'week01_python_tables.ipynb',[26,27,38,39,40,41,42,43,44,53,54,55],'followup-dirty-csv','20ml 정리·변경된 열·새 CSV 선택은 학생 작성'),
 ('평균·분산·단위·ddof',[5,6,7,8],'week01_python_tables.ipynb',[5,6,7,8,47,48,53,55,67,68],'followup-statistics','기호·유도 확인, 새 분산/이동/배율 문제는 학생 풀이'),
 ('axis·shape·reshape·전치·broadcast',[9,10,11,12],'week01_python_tables.ipynb',[58,59,60,61,62,63,64,65,66],'followup-array-A','같은 shape의 다른 값·새 행/열 보정·오류'),
 ('실제 그래프·분포·범주 비교',[13,14],'week01_python_tables.ipynb',[49,50,51,52,53,55,67,68,69,70,71,72,73,74,75,76],'followup-viz-B','Matplotlib/Seaborn 입력변경·좌표·점/막대 설명'),
 ('집계·관측 개수·병합·키',[1,2,3,4,25,26,28],'week01_python_tables.ipynb',[53,54,55,77,78,79],'followup-merge-C','count/size·결측 높이·미상/중복 키 결과는 학생 작성'),
 ('함수 명세·벡터/내적·순서',[5,6,15,16],'week01_python_tables.ipynb',[80,81,82,83,84,85,86],'followup-function-dot-DE','recorded_mean과 새 수량/단가 순서 문제는 학생 작성'),
 ('행렬 수축·위치/ID',[9,10,15,16,25,26],'week01_axes_linear_bridge.ipynb',[20,21,22,23,24,25,26,27],'followup-bridge-A / followup-bridge-B','필수 A/B 새 선형변환·검색을 학생 작성; 선택 stack/lookup 제외'),
 ('실제 학습·훈련/검증 경계',[17,18,19,20,21,22,23,24],'week01_integrated.ipynb',[29,30,31,32],'candidate-15ab-main-oracles','새 문자열 라벨·?·평균·모델·검증 설명'),
 ('ID·물리 CSV·명세 전이',[25,26,27,28,29,30,31,32],'week01_integrated.ipynb',[29,30,31,32],'candidate-15ab-main-oracles','다른 헤더/ID 요구 순서·문자열 예측·오류 처리')]
mapping=[dict(goal=g,integration_cells=ic,followup_file=f,followup_cells=fc,execution_case=c,open_assessment=o,student_completed=False) for g,ic,f,fc,c,o in map_rows]
counts=[]
for path in [ROOT/'lessons/week01/week01_python_tables.ipynb',ROOT/'lessons/week01/week01_axes_linear_bridge.ipynb',ROOT/'lessons/week01/week01_problem_pipeline.ipynb',nb]:
    n=nbformat.read(path,as_version=4);counts.append({'path':str(path.relative_to(ROOT)),'cells':len(n.cells),'code_cells':sum(c.cell_type=='code' for c in n.cells),'source_characters':sum(len(c.source) for c in n.cells)})
report={'source_sha256':expected,'html_matches_fresh_export':True,'relative_links_exist_locally':links,'entrypoint_plan_sha256':sha(ROOT/'curriculum/student-plan.html'),'plan_week1_link_updated_and_historical_timing_clarified':True,'other_plan_content_unchanged':True,'old_plan_baseline_status':'stale for changed week1; not transferred approval','plots':plots,'protected_originals_unchanged':True,'preservation':preservation,'goal_mapping':mapping,'size_metrics':counts,'limits':['Source length and fewer required complete readings are design observations, not measured workload reduction','Student answers remain blank; followup provided cells running does not complete their independent tasks','Relative local links exist; remote publication and full browser visual layout unverified']}
(OUT/'static-and-goal-mapping.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'html_equal':True,'links':links,'plots':plots,'source_characters':counts[-1]['source_characters'],'mapping_goals':len(mapping)},ensure_ascii=False))
