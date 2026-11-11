"""Run each published follow-up path in a distinct subprocess and fresh kernel.
No student answer is supplied: empty code cells are executed as empty cells and remain open.
"""
from pathlib import Path
import json,hashlib,subprocess,sys,concurrent.futures
import nbformat
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[2]
main=ROOT/'lessons/week01/week01_python_tables.ipynb';bridge=ROOT/'lessons/week01/week01_axes_linear_bridge.ipynb'
main_book=nbformat.read(main,as_version=4);bridge_book=nbformat.read(bridge,as_version=4)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(main)=='ee8279b1af621c22da5094d765ea424171c5448527d931b943a6a30cb7c2f6b7'
assert sha(bridge)=='09efa4d1a8ebf918dab7fc0b30f60f8130e817729d70cfe93cd7c60f15b5767f'
prepare=[3,27,54]
common="""assert 'sunlight_hours' in plants.columns and 'light_h' not in plants.columns
assert plants.loc[plants.pot_id=='P05','water_ml'].item()==20
assert plants.loc[plants.pot_id=='P05','height_cm'].item()==10
assert new_plants.columns.tolist()==['sample_id','site','light_hours','water_amount_ml','final_height_cm']
print('original data re-created in a separate fresh kernel; not integration plants')
"""
cases=[
 ('followup-python',main,main_book,prepare+[19,20,22,24],common+"assert returned==6 and shown is None\nassert mean_of_numbers([2,4,6])==4\nassert 'shifted_mean' not in globals()\n",[24]),
 ('followup-statistics',main,main_book,prepare+[46,48],common+"assert np.isclose(lengths.var(ddof=0),8/3)\nassert pd.Series(lengths).var(ddof=0)==lengths.var(ddof=0)\nassert pd.Series(lengths).var(ddof=1)!=lengths.var(ddof=0)\n",[]),
 ('followup-dirty-csv',main,main_book,prepare+[39,41,43],common+"assert dirty_plants.loc[dirty_plants.pot_id=='P02','water_ml'].item()=='20ml'\nassert plants.loc[plants.pot_id=='P02','water_ml'].item()==20\nprint('dirty input provided; student cleaning not completed')\n",[]),
 ('followup-array-A',main,main_book,prepare+[59,61,64,66],common+"assert two_by_three.shape==(2,3) and grid.shape==(3,2)\nassert 'task_array' not in globals()\nprint('student reshape/broadcast answers remain unfilled')\n",[61,66]),
 ('followup-viz-B',main,main_book,prepare+[69,71,73,74],common+"assert place_summary['count'].tolist()==[3,3]\nassert set(place_summary.index)==set(['실내','창가'])\nprint('provided visualization examples run; changed-input student plots not completed')\n",[]),
 ('followup-merge-C',main,main_book,prepare+[78],common+"assert site_notes.site.tolist()==['실내','창가']\nassert len(new_plants)==4\nassert 'joined' not in globals()\nprint('merge inputs prepared; student groupby/merge/new-key answers remain open')\n",[]),
 ('followup-function-dot-DE',main,main_book,prepare+[81,84],common+"assert 'recorded_mean' not in globals()\nassert quantities @ unit_prices==3500\nprint('provided dot example run; function/new price-order answers not completed')\n",[81]),
 ('followup-bridge-A',bridge,bridge_book,[2,21,23],"assert X_new.shape==(3,2) and W_new.shape==(2,2) and bad_W.shape==(3,2)\nprint('bridge A inputs only; empty student code not completed')\n",[23]),
 ('followup-bridge-B',bridge,bridge_book,[2,25,27],"assert query_new.shape==(2,2) and gallery_new.shape==(4,2)\nassert g_ids_new.tolist()==[90,8,53,17]\nprint('bridge B inputs only; empty student code not completed')\n",[27])]
variant_dir=OUT/'followup-inputs';variant_dir.mkdir(exist_ok=True)
requests=[]
for name,source,book,indices,oracle,blanks in cases:
    variant=nbformat.v4.new_notebook(cells=[book.cells[i] for i in indices]);p=variant_dir/(name+'.ipynb');nbformat.write(variant,p)
    op=variant_dir/(name+'-oracle.py');op.write_text(oracle)
    requests.append(dict(name=name,source=str(source.relative_to(ROOT)),source_sha256=sha(source),indices=indices,student_blank_cells=blanks,input_path=p,input_sha256=sha(p),oracle_path=op))
def run(request):
    command=[sys.executable,'-B',str(OUT/'execute_case.py'),'--notebook',str(request['input_path']),'--expected-sha',request['input_sha256'],'--case',request['name'],'--oracle',str(request['oracle_path'])]
    proc=subprocess.run(command,capture_output=True,text=True,timeout=150)
    (OUT/(request['name']+'-stdout.txt')).write_text(proc.stdout);(OUT/(request['name']+'-stderr.txt')).write_text(proc.stderr)
    raw=json.loads((OUT/'cases'/request['name']/'result.json').read_text())
    return {k:v for k,v in request.items() if k not in ('input_path','oracle_path')} | dict(process_exit=proc.returncode,status=raw['status'],student_answers_completed=False,student_learning_observed=False)
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
    results=list(pool.map(run,requests))
report={'integration_candidate_sha256':'15ab0101edbca3c0c669e551cb723b401d168d9730523fa1ac1263a0d7538120','reference':'candidate cell33 title/first-code instructions; teacher exact 0-based indices','cases':results,'all_provided_paths_runnable':all(r['status']=='passed' for r in results),'student_independent_answers_completed':False,'each_case_new_subprocess_and_kernel':True}
(OUT/'followup-path-results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(report,ensure_ascii=False,indent=2))
sys.exit(0 if report['all_provided_paths_runnable'] else 1)
