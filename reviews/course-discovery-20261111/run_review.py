"""Replay additive source discovery and review. Only this review directory is written.
Web searches and semantic judgments are actual agent work represented by notes;
this program does not perform web discovery, authenticate authors, or measure learning.
"""
import argparse, copy, hashlib, json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'tools'))
import discovery_loop as loop

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def rel(p): return str(p.relative_to(ROOT))
def save(p,obj):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
def write_once(p,text):
    if p.exists() and p.read_text()!=text: raise ValueError('Refuse to replace input '+str(p))
    p.parent.mkdir(parents=True,exist_ok=True); p.write_text(text)
def nlines(p): return len(p.read_text().splitlines())
EXTRACTOR='/root/course_discovery/verify_new_scope'
REVIEWER='/root/course_discovery'
SOURCES=[
 {'id':'C01','uri':'https://kitpa.org/koai/2027','revision':'2026-11-11 direct web read; mutable national 2027 announcement','kind':'official_scope','note':'''# C01 national scope reading note
Reader/extractor: /root/course_discovery/verify_new_scope; reviewer /root/course_discovery separately reviewed actual lessons.
URL: https://kitpa.org/koai/2027
Read extent: web lines 90–100, 120–140, 218–234 on 2026-11-11 UTC.
The current national 2027 announcement links /koai/syllabus. It specifies subjects 1–4, 80 selected-response and 10 written-response questions in three hours, and two code-writing questions in three hours.
Its linked syllabus still labels its body IOAI 2026. The extractor also read /koai/syllabus lines 72–196: practical work includes choosing when to use a technique and interpreting its output, beyond calling a library.
These formats justify separate explanation/calculation and implementation evidence. They do not reveal the exact future questions or establish this course's feasibility.
Official 2027 international syllabus link exists, but direct open and link click returned HTTP 429. No full 2027-PDF re-read or domestic adoption claim is made.
This is a paraphrased reading note, not an authenticated original snapshot. Its SHA proves only these local bytes.
'''},
 {'id':'C02','uri':'https://raw.githubusercontent.com/IOAI-official/IOAI-2025/main/Individual-Contest/Pixel/Pixel.ipynb','revision':'2025 individual contest; mutable main read 2026-11-11; no upstream commit pin','kind':'official_problem','note':'''# C02 Pixel reading note
Reader/extractor: /root/course_discovery/verify_new_scope; independently re-read by /root/course_discovery.
URL: https://raw.githubusercontent.com/IOAI-official/IOAI-2025/main/Individual-Contest/Pixel/Pixel.ipynb
Read extent: raw lines 28–90; extractor additionally read displayed 94–96. Markdown cell 4509a190.
Input images are 224 by 224 and have tracking IDs. Output one rectangle per image, top/left inclusive and bottom/right exclusive; at most 6.25 percent of original pixels may be retained. The resulting maximum is 3136 pixels. The output notebook must generate the specified JSONL file.
Observable demand: predict the selected pixel set and (bottom-top)*(right-left), then check boundary, over-budget and file-contract cases on new coordinates. A valid rectangle does not establish CLIP classification quality.
The statement also specifies provided CLIP/data only, an added other class and an eight-minute runtime for 698 test images. They were read, but no dataset/model/runtime experiment was performed.
Empty rectangles and coordinate dtype acceptance were not settled in this read extent. This is a paraphrased reading note, not fetched notebook bytes or an authenticated original snapshot.
'''},
 {'id':'C03','uri':'https://raw.githubusercontent.com/IOAI-official/IOAI-2025/main/Individual-Contest/Antique/Antique.ipynb','revision':'2025 individual contest; mutable main read 2026-11-11; no upstream commit pin','kind':'official_problem','note':'''# C03 Antique reading note
Reader/extractor: /root/course_discovery/verify_new_scope; independently re-read by /root/course_discovery.
URL: https://raw.githubusercontent.com/IOAI-official/IOAI-2025/main/Individual-Contest/Antique/Antique.ipynb
Read extent: raw lines 19–72, statement markdown cell a4c6054c-d42b-4c2b-bb79-deb64d936c24.
There are five feature columns and a label column. Label 1 means authentic, -1 replica, and 0 unknown. Unknown is not a confirmed negative class. Outputs must contain -1 or 1, with the stated file and header contract; accuracy divides correct predictions by all evaluated examples.
The task motivates using unknown-label training samples. An introductory known-label-only supervised example can teach a boundary, but does not solve the complete semi-supervised problem.
Observable introductory demand: classify unknown/negative/positive correctly, exclude target columns from features, and preserve the permitted output-label set in an independent new table.
This is a paraphrased reading note, not original notebook bytes. No contest data/model execution or performance measurement occurred.
'''},
 {'id':'C04','uri':'https://cs229.stanford.edu/summer2019/ps1.pdf','revision':'CS229 Summer 2019 PS1; problem 2; direct web read 2026-11-11','kind':'research','note':'''# C04 primary theory reading note
Reader/extractor: /root/course_discovery/verify_new_scope; independently re-read by /root/course_discovery.
URL: https://cs229.stanford.edu/summer2019/ps1.pdf
Read extent: problem 2, printed pages 5–6, web lines 195–354.
The problem distinguishes hidden true t from observed y. Observed y=0 mixes true negatives and unobserved positives. It assumes p(y=1|t=1,x)=alpha constant over x, with no false observed positives. Those assumptions support p(t=1|x)=p(y=1|x)/alpha and a conditional-probability derivation task.
Introductory transfer: unknown does not entail negative. Advanced transfer: state the observation assumptions before applying a correction; if selection probability depends on x, the constant-alpha correction has not been justified.
Antique does not assert this positive-only observation model. We do not transfer the formula to it. Full Bayes derivation is outside the new introductory label-semantics demand, remains an explicitly unsatisfied advanced question, and is not a national mandate inferred from this university source.
This is a paraphrased reading note, not PDF bytes. No student answer or learning result was observed.
'''}]
DEMANDS=[
 {'id':'N01','statement':'개념의 사용 시점·출력 의미를 이론 설명과 코드 구현에서 각각 평가하기','prerequisites':['표의 행·열과 함수 입출력','기본 비율과 계산 순서'],'learning_demand':'같은 개념을 언제 사용하고 출력이 무엇을 뜻하는지 설명한 뒤 코드와 연결한다.','assessment_demand':'예시를 가린 새로운 입력에서 비코딩 계산·이유와 구현 결과를 각각 남긴다.','dimensions':[{'id':'modality','required_behavior':'비코딩 이유와 코드 결과를 별도 근거로 보존한다.'}],'source_locations':['C01 national announcement L218–234; linked syllabus L83–85'],'interpretation':'Course design transfer from exam modalities; not a claim about undisclosed exact exam questions.'},
 {'id':'N02','statement':'반열린 이미지 사각형·면적 예산·제출 계약을 함께 점검하기','prerequisites':['행·열 인덱스','정수 구간과 곱셈','비율'],'learning_demand':'좌상단 포함·우하단 제외를 픽셀 집합과 연결하고 (bottom-top)*(right-left)로 면적과 6.25% 예산을 판정한다.','assessment_demand':'새 사각형의 경계·상한 초과 사례를 손으로 예측하고 slice 및 지정 출력 구조와 비교한다.','dimensions':[{'id':'contract','required_behavior':'각 이미지당 한 사각형과 좌표 의미·출력 계약을 동시에 확인한다.'}],'source_locations':['C02 raw L28–90'],'interpretation':'Additional official task family; not immediate Week1 or Week2 mandatory content.'},
 {'id':'N03','statement':'미상 라벨을 확정 음성과 구분하고 특성·출력 라벨 경계를 보존하기','prerequisites':['입력 특성과 목표 구분','조건 선택과 행 대응'],'learning_demand':'주어진 라벨 명세에서 unknown과 negative를 구분하고 목표 열을 특성에서 빼며 미상 학습 행 처리 규칙을 명시한다.','assessment_demand':'새 표에서 미상 행·허용 출력 라벨을 판단하고 코드와 이유를 독립 작성한다.','dimensions':[{'id':'assumptions','required_behavior':'알려진 라벨만 쓰는 축소 지도학습 규칙을 공식 문제 전체 해결과 구별한다. PU 상수 alpha 공식을 일반 미상 라벨에 자동 적용하지 않는다.'}],'source_locations':['C03 raw L19–72','C04 printed pp5–6'],'interpretation':'Narrow introductory demand; full semi-supervised model training and probability derivation remain open.'}]
QUESTIONS=[
 'Domestic 2027 syllabus body still says IOAI 2026; applicability of the international 2027 changes and full PDF difference remain unverified after HTTP 429.',
 'Pixel empty-rectangle/dtype rules, full CLIP quality, runtime and actual submission environment remain untested.',
 'The new label-semantics unit does not establish complete semi-supervised learning or the positive-only probability derivation; actual later teaching remains to be read.',
 'Student independent transfer, help received, completion time and learning effects remain unobserved.'
]

def prepare():
 for s in SOURCES:
    p=OUT/'inputs'/('reading-note-'+s['id']+'.md'); write_once(p,s['note']); s['path']=rel(p)
    s['attribution']='Direct web reading/extraction by '+EXTRACTOR+'; reviewer independently re-read selected original spans. Program opens this paraphrased note only; no source authentication.'
 save(OUT/'source-manifest.json',[{k:v for k,v in s.items() if k!='note'}|{'local_note_sha256':sha(ROOT/s['path'])} for s in SOURCES])
 save(OUT/'new-demands.json',DEMANDS)

class Run:
 def __init__(self,name,state):
    self.path=OUT/'runs'/name
    if self.path.exists(): raise ValueError('Use a new --run directory: '+name)
    self.path.mkdir(parents=True); self.state=state; self.seq=0; self.transitions=[]
    save(self.path/'session-00.json',state)
 def event(self,op,**data):
    self.seq+=1; ev={'id':f'course-{self.path.name}-{self.seq:03d}-{op}','op':op,'data':{'reason':'Actual sampled external source review; material design only, no student achievement claim.',**data}}
    save(self.path/'events'/f'{self.seq:03d}-{op}.json',ev)
    self.state=loop.step(self.state,ev,ROOT)
    self.state=json.loads(json.dumps(self.state))
    save(self.path/f'session-{self.seq:02d}.json',self.state)
    r=loop.inspect(self.state,ROOT); self.transitions.append({'event':ev['id'],'status':r['status'],'next_action':r['next_action']})
    return ev['id']
 def external(self,fid):
    self.event('discover',frontier_id=fid,query='New national 2027 modality and previously unreviewed Pixel/Antique task families plus original CS229 positive-only theory; direct web read 2026-11-11',actor=EXTRACTOR,outcome='found',candidates=[{k:v for k,v in s.items() if k!='note'} for s in SOURCES])
    reads=[self.event('read',source_id=s['id'],actor=EXTRACTOR,start_line=1,end_line=nlines(ROOT/s['path'])) for s in SOURCES]
    self.event('trace',frontier_id=fid,read_ids=reads,actor=EXTRACTOR,rationale='Independent extractor supplied these external operations before lesson comparison; reviewer retains the narrower introductory interpretation explicitly.',counterevidence='International past tasks do not govern the exact domestic 2027 exam. Week1 foundations are legitimate; scheduled later placement is not delivery.',uninvestigated=QUESTIONS,demands=DEMANDS)
 def compare(self,did,judgment,observed,span=None,dim_spans=None,dim_judgments=None):
    lesson=ROOT/self.state['seed']['scope']['lesson_path']; sp=span or (1,nlines(lesson)); demand=loop.replay(self.state)['demands'][did]
    dims=[]
    for d in loop.demand_dimensions(demand):
      ds=(dim_spans or {}).get(d['id'],sp)
      dj=(dim_judgments or {}).get(d['id'],'met' if judgment=='covered' else 'uncertain' if judgment=='uncertain' else 'gap')
      dims.append({'id':d['id'],'judgment':dj,'observed_behavior':observed,'rationale':'Manual content judgment by independent reviewer. The file receipt verifies bytes and span only; neither semantic entailment nor learner mastery is machine proven.','start_line':ds[0],'end_line':ds[1]})
    self.event('compare',demand_id=did,reviewer=REVIEWER,judgment=judgment,rationale=observed,start_line=sp[0],end_line=sp[1],dimensions=dims)
 def finish(self):
    report=loop.inspect(self.state,ROOT); save(self.path/'session.json',self.state);save(self.path/'report.json',report);save(self.path/'manifest.json',loop.manifest(self.state));save(self.path/'transitions.json',self.transitions)
    return report

def main():
 ap=argparse.ArgumentParser();ap.add_argument('mode',choices=['baseline','plan']);ap.add_argument('--run',required=True);a=ap.parse_args();prepare()
 prior=ROOT/'reviews/discovery-loop-20261111/runs/session.json'; old=json.loads(prior.read_text()); old_report=loop.inspect(old,ROOT)
 if a.mode=='baseline':
    r=Run(a.run,copy.deepcopy(old));save(r.path/'origin.json',{'prior_session_path':rel(prior),'prior_file_sha256':sha(prior),'prior_session_digest':old_report['session_sha256'],'prior_events':len(old['events']),'inherited_queue':[q['demand_id'] for q in old_report['queue']],'prior_scope_unchanged':True});r.external('next-wave')
    r.compare('N01','uncertain','Week1 has explanatory prompts and coding, but their presence does not establish all-course dual-modality evaluation or new unseen-exam transfer. Original scope is course readiness.')
    r.compare('N02','gap','Whole preserved Week1 projection was reviewed: basic array/axis foundations exist; no rectangle area-budget and JSONL submission task is implemented.')
    r.compare('N03','gap','Whole preserved Week1 projection distinguishes input/target and prediction time, but the new unknown-versus-negative label and permitted-output exercise is absent.')
 else:
    p=ROOT/'curriculum/student-plan.html'; snapshot=OUT/'inputs'/'student-plan.html';write_once(snapshot,p.read_text())
    config={'schema_version':1,'synthetic':False,'scope':{'id':'course-plan-sampled-frontier','lesson_path':rel(snapshot),'artifact_path':rel(p),'artifact_sha256':sha(p),'lesson_revision':'plan-'+sha(p)[:12],'readiness':'course','boundary':'Actual ten-week scheduling document only; planned teaching and evaluation are not delivered lessons or student results.'},'frontier':[{'id':'next-wave','question':'Does the actual ten-week plan account for newly sampled official task/theory requirements?','required_kinds':['official_scope','official_problem','research']}],'policy':{'max_events':100,'max_rounds':20,'max_no_progress':8,'max_elapsed_minutes':180}}
    save(OUT/'plan-config.json',config);r=Run(a.run,loop.initialize(config));r.external('next-wave')
    for did,obs in [('N01','Plan line 94 announces weekly selected/written questions and coding. These are scheduled activities; actual artifacts, item validity and student work are not supplied by this plan.'),('N02','Weeks7/9/10 schedule image/CLIP/submission topics, but no explicit half-open area-budget task and independent boundary assessment is delivered in the plan.'),('N03','Week2 schedules split/preprocessing/metrics, but unknown-label semantics and its independent new-table assessment are not explicit delivered materials in the plan.')]:r.compare(did,'gap',obs)
    save(r.path/'origin.json',{'plan_raw_sha256':sha(p),'plan_path':rel(p),'contract_path':'curriculum/contract.json','contract_sha256':sha(ROOT/'curriculum/contract.json'),'contract_60_rows_status':'scheduled_only','legacy_queue_preserved_at':rel(prior)})
 report=r.finish();print(json.dumps({'run':rel(r.path),'status':report['status'],'ready_for_review':report['ready_for_review'],'queue_count':len(report['queue']),'open_questions':len(report['open_questions']),'next_action':report['next_action'],'events':report['usage']['events']},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
