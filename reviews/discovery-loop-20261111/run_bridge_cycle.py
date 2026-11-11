"""A scoped baseline -> authored bridge -> seeded missing-assessment comparison.
Semantic verdicts below are the root's explicit review of these actual files;
the discovery reducer tracks them and does not generate them from prose.
"""
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'tools'));import discovery_loop as loop

def save(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def rel(p):return str(p.relative_to(ROOT))
def count(p):return len(p.read_text().splitlines())
notes=OUT/'inputs/numpy-matmul-note.md'
notes.write_text('''# Primary-document reading note: NumPy matmul
URL: https://numpy.org/doc/stable/reference/generated/numpy.matmul.html
Version: v2.5, accessed 2026-11-11. Actual browser read: signature, exceptions and 2D notes/examples.
This is an operator paraphrase, not an original-source copy or authenticated document.
For two 2D inputs, a shared contraction dimension is summed. Shapes (n,d) and (d,m) produce (n,m). A mismatching shared dimension raises an error. For this probe, the library contract supports comparing each query row against each gallery row after transpose. It says nothing about semantic correctness of arbitrary feature order or gallery IDs. Those are explicit task and data contracts.
''')
candidate=OUT/'candidate-bridge.md'
fault=OUT/'inputs/bridge-missing-assessment.md';text=candidate.read_text();start=text.index('## 새 독립 과제');end=text.index('## 별도 검토: 과제 예시 답안');fault.write_text(text[:start]+'## 삭제된 평가 영역\n이 오류 control에는 새 입력 평가가 없습니다.\n\n'+text[end:])
sources=[{'id':'problem','uri':'https://raw.githubusercontent.com/IOAI-official/IOAI-2025/main/Individual-Contest/Restroom/Restroom.ipynb','path':rel(OUT/'inputs/reading-note-S05.md'),'revision':'IOAI2025 accessed2026-11-11','kind':'official_problem','attribution':'Direct primary reading by research agent, checked by root; this local file is a paraphrased note.'},
 {'id':'math','uri':'https://numpy.org/doc/stable/reference/generated/numpy.matmul.html','path':rel(notes),'revision':'NumPy2.5 accessed2026-11-11','kind':'research','attribution':'Root directly read official documentation; local file is the recorded paraphrase.'}]
results={}
for label,path in [('baseline',OUT/'inputs/lesson-source.md'),('candidate',candidate),('missing_assessment',fault)]:
 config={'schema_version':1,'synthetic':False,'scope':{'id':'bounded-pairwise-bridge-'+label,'lesson_path':rel(path),'readiness':'scoped_foundation','boundary':'Only rectangular pairwise dot-product and row/column-ID correspondence. This does not retire the broader D05/course queue or prove cosine retrieval, training or learner mastery.','lesson_revision':label},'frontier':[{'id':'external-operation','question':'What must a small pairwise-score and ID bridge explain from an actual external retrieval task?','required_kinds':['official_problem','research']}],'policy':{'max_events':20,'max_rounds':5,'max_no_progress':5,'max_elapsed_minutes':60}}
 state=loop.initialize(config)
 def step(i,op,data):
  global state
  state=loop.step(state,{'id':label+'-'+str(i),'op':op,'data':{'reason':'Actual reviewed content; fixed requirement and same source access across variants.',**data}},ROOT)
  state=json.loads(json.dumps(state))
 step(1,'discover',{'frontier_id':'external-operation','query':'Original Restroom task and official NumPy matrix-product contract','actor':'external-requirement-reader','outcome':'found','candidates':sources})
 for i,s in enumerate(sources,2):step(i,'read',{'source_id':s['id'],'actor':'external-requirement-reader','start_line':1,'end_line':count(ROOT/s['path'])})
 demand={'id':'pairwise-id-bridge','statement':'Compute a rectangular all-pairs dot-product score matrix and restore actual gallery IDs after row reordering.','prerequisites':['same-order vector dot products','2D shape and transpose'],'learning_demand':'Explain contraction and retained axes, compute one score by hand and map score positions to IDs.','assessment_demand':'Design a different rectangular-input and ID-permutation task, with an explicit teacher key and help conditions; actual learner performance is not asserted.','dimensions':[{'id':'principle','required_behavior':'Define S_ij=sum_k Q_ik G_jk and (n,d)@(d,m)->(n,m).'}, {'id':'practice','required_behavior':'Check changed gallery order with IDs moved together and contrast elementwise multiplication.'}]}
 step(4,'trace',{'frontier_id':'external-operation','read_ids':[label+'-2',label+'-3'],'actor':'external-requirement-reader','rationale':'A vector-dot mention alone does not imply all-pairs contraction or ID mapping.','counterevidence':'The official baseline is not an optimal or universally correct recipe; this probe covers only a stated synthetic numeric bridge.','uninvestigated':[],'demands':[demand]})
 dims=[]
 for d in loop.demand_dimensions(demand):
  verdict='met' if label=='candidate' else ('gap' if d['id']=='assessment' else 'met') if label=='missing_assessment' else 'met' if d['id']=='prerequisites' else 'gap'
  dims.append({'id':d['id'],'judgment':verdict,'observed_behavior':('Prior lesson provides vector dot/transpose only.' if label=='baseline' else 'The bridge provides symbols, rectangular trace, executable examples and ID-reorder controls.' if d['id']!='assessment' or label=='candidate' else 'The independent task section was deliberately removed while explanations/key remain.'),'rationale':'Root reviewed actual content and independently checked the displayed 2x4 scores and ID alignment. Assessment is material design only; answer concealment is a delivery condition, not enforced by this Markdown.','start_line':1,'end_line':count(path)})
 step(5,'compare',{'demand_id':demand['id'],'reviewer':'root-independent-material-review','judgment':'covered' if label!='baseline' else 'gap','rationale':'Fixed narrow criterion; candidate authored by Terra, root inspected it. This scoped finding cannot close the original course frontier.','start_line':1,'end_line':count(path),'dimensions':dims})
 report=loop.inspect(state,ROOT);save(OUT/'bridge-cycle'/f'{label}-state.json',state);save(OUT/'bridge-cycle'/f'{label}-report.json',report)
 results[label]={'expected':'recorded_ready' if label=='candidate' else 'needs_work','actual':report['status'],'ready':report['ready_for_review'],'queue_reasons':[q['reasons'] for q in report['queue']]}
 assert results[label]['expected']==results[label]['actual']
course=json.loads((OUT/'runs/final-report.json').read_text());assert not course['ready_for_review'] and 'D05' in {x['demand_id'] for x in course['queue']}
summary={'status':'passed','variants':results,'original_course_D05':'still_unresolved','candidate_sha256':hashlib.sha256(candidate.read_bytes()).hexdigest(),'implementation_sha256':hashlib.sha256((ROOT/'tools/discovery_loop.py').read_bytes()).hexdigest(),'limits':['Only one scoped design bridge was improved, not the whole lesson/course.','The missing-assessment case is a deliberate material fault reviewed by root; automatic semantic fault detection is not claimed.','The candidate is a review fixture; user lesson files are unchanged.']};save(OUT/'bridge-cycle-results.json',summary);print(json.dumps(summary,ensure_ascii=False,indent=2))
