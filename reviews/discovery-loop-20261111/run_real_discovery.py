"""Execute the discovery reducer on direct-read research and the preserved actual lesson.

The source files below are versioned research NOTES, not fetched originals. Original
reading/search happened through browser tools and is attributed in source-research.
This replay does not manufacture a new web search or authenticate its author's judgment.
"""
import copy, hashlib, json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'tools'))
import discovery_loop as loop

def save(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
def rel(path): return str(path.relative_to(ROOT))
def lines(path): return len(path.read_text().splitlines())
def source_kind(s):
    return 'official_scope' if s['family'] in ('national_scope','international_scope') else 'official_problem' if s['family'].startswith(('national_examples','international_task')) else 'research'
research=json.loads((OUT/'source-research.json').read_text())
sources={s['source_id']:s for s in research['sources']}
demands={d['demand_id']:d for d in research['demands']}
notes={}
for sid,s in sources.items():
    path=OUT/'inputs'/('reading-note-'+sid+'.md')
    path.write_text('# Direct-read research note '+sid+'\n\nThis is the research agent\'s paraphrased reading record, not an original-source snapshot.\n\n'+json.dumps(s,ensure_ascii=False,indent=2)+'\n')
    notes[sid]={'id':sid,'uri':s['url'],'path':rel(path),'revision':s['version'],'kind':source_kind(s),
                'attribution':'Source-research Sol agent directly read the original at recorded extent. Program reads this note only; official status/entailment are not authenticated.'}
lesson=OUT/'inputs/lesson-source.md'
artifact=OUT/'inputs/preserved-lesson.ipynb'
config={'schema_version':1,'synthetic':False,'scope':{'id':'KOAI-course-external-frontier','lesson_path':rel(lesson),
    'artifact_path':rel(artifact),'artifact_sha256':hashlib.sha256(artifact.read_bytes()).hexdigest(),
    'readiness':'course','boundary':'A sampled external requirement audit of the course; only Week1 actual material is available. Later scheduling is not achieved coverage.',
    'lesson_revision':'preserved-733c0093'},'frontier':[
      {'id':'scope','question':'Which target scope and source-version applicability issues are outside the current lesson?','required_kinds':['official_scope']},
      {'id':'problems','question':'What operations do actual official problems require beyond named lesson examples?','required_kinds':['official_problem']},
      {'id':'mechanisms','question':'What prerequisites, formulas and assessment operations do primary technical references expose?','required_kinds':['research']}],
    'policy':{'max_events':120,'max_rounds':20,'max_no_progress':8,'max_elapsed_minutes':180}}
save(OUT/'runs/config.json',config)
state=loop.initialize(config); serial=0; outputs=[]
def event(op,data):
    global state,serial
    serial+=1
    raw={'id':f'actual-{serial:03d}-{op}','op':op,'data':{'reason':'Current direct-read research and actual-lesson review; design evidence, no learner claim.',**data}}
    save(OUT/'runs/events'/f'{serial:03d}-{op}.json',raw)
    state=loop.step(state,raw,ROOT)
    state=json.loads(json.dumps(state)) # every transition survives an actual serialized restart
    save(OUT/'runs/session.json',state)
    outputs.append({'event':raw['id'],'status':loop.inspect(state,ROOT)['status'],'next_action':loop.inspect(state,ROOT)['next_action']})
    return raw['id']
def lesson_span(did, dimension='learning'):
    # Each receipt binds the whole file SHA and reads a precise precursor/task cell.
    # A missing-content judgment remains the researcher's whole-source semantic review,
    # not a claim that a short excerpt mechanically proves absence.
    anchors=demands[did]['current_lesson_locators']
    cid=anchors[-1]['cell_id'] if dimension in ('practice','assessment') else anchors[0]['cell_id']
    text=lesson.read_text().splitlines()
    starts=[i for i,line in enumerate(text) if line.startswith('## Cell ') and (': '+cid+' (') in line]
    start=starts[0] if starts else 0
    end=next((i for i in range(start+1,len(text)) if text[i].startswith('## Cell ')),len(text))
    return start+1,end

def extract(fid,dids):
    ids=sorted({sid for did in dids for sid in demands[did]['source_ids']})
    event('discover',{'frontier_id':fid,'query':' | '.join(sources[sid]['url'] for sid in ids),'actor':'source-research-sol','outcome':'found','candidates':[notes[sid] for sid in ids]})
    reads={}
    for sid in ids:
        existing=[rid for rid,r in loop.replay(state)['reads'].items() if r['source_id']==sid]
        reads[sid]=existing[-1] if existing else event('read',{'source_id':sid,'start_line':1,'end_line':lines(ROOT/notes[sid]['path']),'actor':'source-research-sol'})
    extracted=[]
    for did in dids:
        d=demands[did]
        extra=[{'id':'principle','required_behavior':d['theory_and_formula']['formula']},
               {'id':'practice','required_behavior':d['practice']['task']}]
        extracted.append({'id':did,'statement':d['title'],'prerequisites':d['prerequisites'],
            'learning_demand':'; '.join(d['reasoning_operation']),
            'assessment_demand':'; '.join(d['independent_assessment_dimensions']),
            'dimensions':extra,'stage_proposal':d['staging'],'source_locations':d['precise_refs']})
    event('trace',{'frontier_id':fid,'read_ids':list(reads.values()),'actor':'source-research-sol',
        'rationale':'Externally derived obligations precede lesson matching. Topic names alone do not discharge the operation.',
        'counterevidence':'Official international tasks and library contracts do not mandate immediate Week1 placement. Existing foundation strengths remain valid.',
        'uninvestigated':['Additional official task families and later actual lessons still need sampling; domestic adoption of the international changes is unresolved.'] if fid=='heldout' else [],'demands':extracted})
    for did in dids:
        d=demands[did]
        judgment='uncertain' if did=='D11' else 'covered' if did=='D03' else 'gap'
        # A narrow material-design control: current input/target/timing explanations exist.
        dims=[]
        for dim in loop.demand_dimensions(next(x for x in loop.replay(state)['demands'].values() if x['id']==did)):
            dimension_judgment='met' if judgment=='covered' else 'uncertain' if judgment=='uncertain' else 'gap'
            if dim['id']=='prerequisites' and judgment!='covered':
                dimension_judgment='met' if did in ('D01','H01','H02') else 'gap' if did=='D08' else 'uncertain'
            dims.append({'id':dim['id'],'judgment':dimension_judgment,
                'observed_behavior':('Existing sums/indexing/return/axis foundations are preserved; full prerequisite-set availability is reviewed separately. ' if dim['id']=='prerequisites' else '')+d['missingness'],
                'rationale':'Reviewed teaching/task DESIGN only. '+d['staging']['rationale'],
                'start_line':lesson_span(did,dim['id'])[0],'end_line':lesson_span(did,dim['id'])[1]})
        event('compare',{'demand_id':did,'judgment':judgment,'reviewer':'root-actual-content-review',
            'rationale':d['missingness']+' Scope is course-level; later placement proposals do not invalidate a proper basic Week1, and do not prove later teaching.',
            'start_line':lesson_span(did)[0],'end_line':lesson_span(did)[1],'dimensions':dims})
extract('scope',['D11'])
extract('problems',['D01','D02','D03','D04','D05','D12'])
extract('mechanisms',['D06','D07','D08','D09','D10'])
first=loop.inspect(state,ROOT);save(OUT/'runs/development-session.json',state);save(OUT/'runs/development-report.json',first)
# The held-out requirements are introduced AFTER the development run. The code has
# no branch for their names. H01 shares Radar (requirement holdout); H02 uses Concepts.
event('frontier',{'probe':{'id':'heldout','question':'Which previously unreviewed scoring and execution-contract requirements change the work queue?','required_kinds':['official_problem']}})
opened=loop.inspect(state,ROOT)
extract('heldout',['H01','H02'])
questions=loop.inspect(state,ROOT)['open_questions']
event('frontier',{'probe':{'id':'next-wave','question':'Review further official task families and later actual lessons; resolve domestic/international applicability.','required_kinds':['official_scope','official_problem']},'resolves':[q['id'] for q in questions]})
final=loop.inspect(state,ROOT);save(OUT/'runs/final-report.json',final);save(OUT/'runs/transitions.json',outputs)
assert len(first['demands'])==12 and len(final['demands'])==14
assert {'H01','H02'} <= {q['demand_id'] for q in final['queue']}
assert final['status']=='needs_work' and not final['ready_for_review']
assert opened['next_action']=='discover_original_sources'
summary={'development_demands':12,'heldout_added':['H01','H02'],'final_demands':14,'final_queue_count':len(final['queue']),
 'status':final['status'],'event_count':len(state['events']),'serialized_restart_each_event':True,
 'frontier_expansion_next_action':opened['next_action'],'remaining_frontier':'next-wave','source_truth':'not_authenticated','learner_mastery':'not_observed',
 'limits':['Sampled source corpus, not completeness of competition knowledge.','Search and semantic reading/extraction are actual agent work recorded here, not automatically executed by this Python reducer.','The original lesson branch is untouched. D03 is a narrow current material-design finding, not task-family transfer or course readiness.']}
save(OUT/'actual-loop-results.json',summary)
print(json.dumps(summary,ensure_ascii=False,indent=2))
