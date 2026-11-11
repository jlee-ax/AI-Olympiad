"""Each source mutation gets a separate subprocess and kernel. Baseline already passed."""
from pathlib import Path
import json,hashlib,subprocess,sys,concurrent.futures,copy
import nbformat
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[2]
source=ROOT/'lessons/week01/week01_integrated.ipynb';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
expected='15ab0101edbca3c0c669e551cb723b401d168d9730523fa1ac1263a0d7538120'
assert sha(source)==expected
control=json.loads((OUT/'cases/candidate-15ab-main-oracles/result.json').read_text());assert control['status']=='passed'
book=nbformat.read(source,as_version=4)
mutations=[
 ('nan_not_missing',6,'if not pd.isna(value):','if value is not None:','source_check'),
 ('zero_discarded',6,'if not pd.isna(value):','if not pd.isna(value) and value != 0:','source_check'),
 ('all_missing_mean_zero',6,'return None','return 0','source_check'),
 ('fit_on_all_rows',18,'filled_train = fill.fit_transform(x_train)','fill.fit(plants[["water_ml"]]); filled_train = fill.transform(x_train)','source_check'),
 ('refit_imputer_on_validation',22,'filled_validation = fill.transform(x_validation)','filled_validation = fill.fit_transform(x_validation)','independent_oracle'),
 ('target_in_model_features',18,'x_train = training[["water_ml"]]','x_train = training[["water_ml", "height_cm"]]','source_check'),
 ('training_targets_reversed',20,'model.fit(filled_train, y_train)','model.fit(filled_train, 1 - y_train)','source_check'),
 ('training_change_ignored',24,'changed_model = NearestCentroid().fit(changed_x, y_train)','changed_model = model','source_check'),
 ('predictions_reversed_without_ids',22,'"prediction": predictions','"prediction": predictions[::-1]','independent_oracle'),
 ('output_row_order_wrong',26,'restored = shuffled.set_index("pot_id").loc[required_order].reset_index()','restored = shuffled.reset_index(drop=True)','source_check'),
 ('extra_csv_index',26,'restored.to_csv(index=False, lineterminator="\\n")','restored.to_csv(index=True, lineterminator="\\n")','independent_oracle'),
 ('physical_csv_replaced_with_memory',28,'restored.to_csv(result_path, index=False)\n    file_check = pd.read_csv(result_path)','file_check = pd.read_csv(StringIO(output_csv))','physical_io_oracle'),
 ('reshape_used_as_transpose',12,'transposed = light_by_day.T','transposed = light_by_day.reshape(2, 3)','source_check')]
inputs=OUT/'mutation-inputs';inputs.mkdir(exist_ok=True)
requests=[]
for name,index,old,new,detector in mutations:
    variant=copy.deepcopy(book);assert variant.cells[index].source.count(old)==1,(name,'replacement must be unique')
    variant.cells[index].source=variant.cells[index].source.replace(old,new)
    p=inputs/(name+'.ipynb');nbformat.write(variant,p)
    requests.append(dict(name=name,source_cell=index,old=old,new=new,detector=detector,input_path=p,input_sha256=sha(p)))
def run(req):
    case='mutant-'+req['name'];command=[sys.executable,'-B',str(OUT/'execute_case.py'),'--notebook',str(req['input_path']),'--expected-sha',req['input_sha256'],'--case',case,'--oracle',str(OUT/'oracle-integration.py')]
    proc=subprocess.run(command,capture_output=True,text=True,timeout=150)
    (OUT/(case+'-stdout.txt')).write_text(proc.stdout);(OUT/(case+'-stderr.txt')).write_text(proc.stderr)
    raw=json.loads((OUT/'cases'/case/'result.json').read_text())
    evaluation={k:v for k,v in req.items() if k!='input_path'}|dict(raw_status=raw['status'],raw_process_exit=proc.returncode,case_result='cases/'+case+'/result.json',harness_error=False)
    if req['detector']=='source_check':
        assert raw['status']=='notebook_error' and raw['failed_cell']>=req['source_cell'],evaluation
        assert raw['error']['ename'] in ['AssertionError','ValueError'],raw['error']
        evaluation.update(status='detected',detected_at_cell=raw['failed_cell'],error=raw['error']['ename']+': '+str(raw['error']['evalue']))
    elif req['detector']=='independent_oracle':
        assert raw['status']=='oracle_error' and raw['error']['ename']=='AssertionError',evaluation
        evaluation.update(status='detected',source_cells_alone_passed=True,error=raw['error']['evalue'])
    else:
        assert raw['status']=='passed',evaluation
        operations=[event['operation'] for event in raw['file_io_events'] if event['path'].endswith('/result.csv') or event['path']=='result.csv']
        assert not operations,evaluation
        evaluation.update(status='detected',source_cells_and_numeric_oracle_passed=True,error='No physical result.csv write/read; memory CSV is not disk I/O')
    return evaluation
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
    results=list(pool.map(run,requests))
report={'source_sha256':expected,'baseline_control':'cases/candidate-15ab-main-oracles/result.json','each_case_new_subprocess_and_kernel':True,'mutations':results,'detected_count':len(results),'notes':'Expected negative failures are preserved as raw notebook_error/oracle_error results, not rewritten as successful notebook execution. Physical-I/O mutant passes source but fails external file audit. No student answers inserted.'}
(OUT/'mutation-results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'source_sha256':expected,'detected_count':len(results),'source_checks':sum(r['detector']=='source_check' for r in results),'independent_oracles':sum(r['detector']!='source_check' for r in results)},ensure_ascii=False))
