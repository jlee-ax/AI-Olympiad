#!/usr/bin/env python3
"""Independent finite-case review. Writes only beside this script; no socket kernel."""
import os, sys, json, hashlib, ast, io, csv, zipfile, itertools, copy, subprocess, shutil, warnings, types
from pathlib import Path
from fractions import Fraction
from datetime import datetime, timezone
ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent
RUNTIME=OUT/('runtime-'+Path(sys.argv[2]).stem if len(sys.argv)>2 and sys.argv[1]=='--worker' else 'runtime')
RUNTIME.mkdir(exist_ok=True)
for name in ['IPYTHONDIR','MPLCONFIGDIR','XDG_CACHE_HOME','JUPYTER_RUNTIME_DIR','TMPDIR','TEMP','TMP']:
    directory=RUNTIME/name.lower(); directory.mkdir(exist_ok=True); os.environ[name]=str(directory)
os.environ['PYTHONDONTWRITEBYTECODE']='1'
os.environ['LOKY_MAX_CPU_COUNT']='1'
os.environ['PYDEVD_DISABLE_FILE_VALIDATION']='1'
import tempfile
tempfile.tempdir=os.environ['TMPDIR']
import nbformat, numpy as np, pandas as pd, sklearn
from nbconvert import HTMLExporter
from ipykernel.inprocess.manager import InProcessKernelManager
from sklearn.impute import SimpleImputer
from sklearn.neighbors import NearestCentroid
from sklearn.naive_bayes import GaussianNB
from sklearn.pipeline import Pipeline
NB=ROOT/'lessons/week01/week01_problem_pipeline.ipynb'
EXPECTED='f64a54c8f8eeb995fa8b85fc565836c5e66a97249f97177644cb15ad8f88997a'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
book=nbformat.read(NB,as_version=4)
assert sha(NB)==EXPECTED
nbformat.validate(book)
tracked=[NB, NB.with_suffix('.html'), NB.with_name('week01_problem_pipeline_teacher.md'),
 ROOT/'lessons/week01/week01_axes_linear_bridge.ipynb',ROOT/'lessons/week01/week01_axes_linear_bridge.html']
before={str(p.relative_to(ROOT)):sha(p) for p in tracked}
checks=[]
def passed(name,**details): checks.append(dict(name=name,status='pass',**details))
def reject(fn):
    try: fn()
    except (ValueError,TypeError,KeyError,zipfile.BadZipFile,UnicodeDecodeError) as e:return type(e).__name__
    raise AssertionError('invalid input unexpectedly accepted')
def visible(c):
    return [('stream',o.name,o.text) if o.output_type=='stream' else ('display',o.data.get('text/plain','')) if o.output_type in ('display_data','execute_result') else ('error',str(o)) for o in c.outputs]
def run(nb,compare=False):
    km=InProcessKernelManager(); km.start_kernel(); shell=km.kernel.shell; cl=km.client(); cl.start_channels()
    audit=[]; old_write=Path.write_bytes; old_read=Path.read_bytes
    def physical_write(path,data):
        result=old_write(path,data)
        if path.name=='submission.zip':
            assert path.resolve().is_relative_to(RUNTIME.resolve())
            audit.append(dict(operation='write',name=path.name,exists=path.exists(),bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),path=str(path.relative_to(OUT))))
        return result
    def physical_read(path):
        data=old_read(path)
        if path.name=='submission.zip':audit.append(dict(operation='read',name=path.name,bytes=len(data),sha256=hashlib.sha256(data).hexdigest()))
        return data
    Path.write_bytes=physical_write; Path.read_bytes=physical_read
    try:
        indices=[]
        for i,c in enumerate(nb.cells):
            if c.cell_type!='code':continue
            cl.execute(c.source,store_history=False); reply=cl.get_shell_msg(timeout=90)
            c.execution_count=reply['content']['execution_count'];c.outputs=[]
            while True:
                m=cl.get_iopub_msg(timeout=90)
                if m['msg_type']=='status' and m['content'].get('execution_state')=='idle':break
                if m['msg_type'] in ('stream','display_data','execute_result','error'):c.outputs.append(nbformat.v4.output_from_msg(m))
            if reply['content']['status']!='ok':raise AssertionError('cell '+str(i)+': '+str(reply['content'].get('ename'))+' '+str(reply['content'].get('evalue')))
            if compare:assert visible(c)==visible(book.cells[i]),'stored output mismatch '+str(i)
            indices.append(i)
        snapshot=shell.user_ns.copy()
        for name in ['new_model','is_missing_id','predict_pairs','align_predictions','csv_text','archive_texts','make_archive','inspect_archive','show_rejected']:
            if name in snapshot:
                fn=snapshot[name]
                snapshot[name]=types.FunctionType(fn.__code__, snapshot, fn.__name__, fn.__defaults__, fn.__closure__)
        return snapshot,nb,indices,audit
    finally:
        Path.write_bytes=old_write; Path.read_bytes=old_read
        cl.stop_channels();km.shutdown_kernel();shell._atexit_once()

def manual_fit(rows,labels):
    # Independent list/Fraction implementation; no sklearn/numpy fit used.
    means=[sum(Fraction(str(row[j])) for row in rows if not pd.isna(row[j]))/sum(not pd.isna(row[j]) for row in rows) for j in range(len(rows[0]))]
    filled=[[means[j] if pd.isna(v) else Fraction(str(v)) for j,v in enumerate(row)] for row in rows]
    centers={k:[sum(row[j] for row,y in zip(filled,labels) if y==k)/labels.count(k) for j in range(len(means))] for k in sorted(set(labels))}
    def pred(query):
        q=[means[j] if pd.isna(v) else Fraction(str(v)) for j,v in enumerate(query)]
        return min(centers,key=lambda k:sum((v-c)**2 for v,c in zip(q,centers[k])))
    return means,centers,pred

def make_model(classifier=None):return Pipeline([('fill',SimpleImputer(strategy='mean')),('classifier',classifier or NearestCentroid())])

if len(sys.argv)>1 and sys.argv[1]=='--worker':
    worker_result={}
    try:
        variant=nbformat.read(sys.argv[2],as_version=4)
        detector=sys.argv[3]
        try:
            mns,mbook,mindices,maudit=run(variant)
            if detector=='independent_bool_oracle':
                assert not mns['align_predictions'](['X'],[('X',True)]),'boolean output accepted as integer'
            elif detector=='independent_physical_io_oracle':
                assert [a['operation'] for a in maudit]==['write','read'],'no physical submission.zip write/read'
            worker_result={'detected':False,'evidence':'all cells and independent detector passed'}
        except AssertionError as error:
            worker_result={'detected':True,'evidence':str(error)}
        print(json.dumps(worker_result,ensure_ascii=False))
    finally:
        shutil.rmtree(RUNTIME,ignore_errors=True)
    sys.exit(0)

try:
    ns,executed,indices,audit=run(copy.deepcopy(book),True)
    assert len(book.cells)==27 and len(indices)==12
    assert [r['operation'] for r in audit]==['write','read']
    assert audit[0]['sha256']==audit[1]['sha256']
    assert not ns['practice_zip'].exists() and not ns['practice_zip'].parent.exists()
    nbformat.write(executed,OUT/'independently-executed.ipynb')
    passed('fresh_inprocess_all_cells_and_saved_outputs',cells=27,code_cells=12,code_indices=indices)
    passed('physical_submission_zip_write_read_cleanup',audit=audit,removed=True)
    answer=book.cells[25]
    assert not ast.parse(answer.source).body and not answer.outputs
    passed('student_answer_blank',actual_student_solution_executed=False)
    main=ns['known_train'];features=ns['feature_cols'];model=ns['model']
    means,centers,manual_predict=manual_fit(main[features].values.tolist(),main.label.tolist())
    assert [float(v) for v in means]==[5,3]
    assert np.allclose(model['fill'].statistics_,[float(v) for v in means])
    assert model['classifier'].classes_.tolist()==sorted(centers)
    assert np.allclose(model['classifier'].centroids_,[[float(v) for v in centers[k]] for k in sorted(centers)])
    assert [manual_predict(r) for r in ns['validation'][features].values.tolist()]==[-1,1,1,1]
    assert ns['val_predictions'].tolist()==[-1,1,1,1] and ns['accuracy']==Fraction(3,4)
    x_changed=main.copy();x_changed.loc[x_changed.row_id=='T4','texture']=11
    y_changed=main.copy();y_changed.loc[y_changed.row_id=='T3','label']=-1
    change_results=[]
    for kind,frame in [('X',x_changed),('y',y_changed)]:
        fitted=make_model().fit(frame[features],frame.label)
        _,_,oracle=manual_fit(frame[features].values.tolist(),frame.label.tolist())
        actual=int(fitted.predict(ns['probe'])[0]);expected=oracle([5.25,3])
        assert actual==expected==-1 and int(model.predict(ns['probe'])[0])==1
        change_results.append(dict(kind=kind,query=[5.25,3],original=1,modified=actual,centers=fitted['classifier'].centroids_.tolist()))
    passed('fraction_oracle_main_fit_predictions_and_training_influence',means=[5,3],centers={'-1':[2,2],'1':[8,4]},validation_accuracy='3/4',changes=change_results)
    modified=ns['training'].copy();modified.loc[modified.label==0,features]=[100000,-100000]
    known=modified[modified.label.isin([-1,1])]
    unchanged=make_model().fit(known[features],known.label)
    assert np.array_equal(unchanged['fill'].statistics_,model['fill'].statistics_)
    assert np.array_equal(unchanged['classifier'].centroids_,model['classifier'].centroids_)
    snapshot=(model['fill'].statistics_.copy(),model['classifier'].centroids_.copy())
    v=ns['validation'].copy();v.loc[0,'texture']=200000;v.label=-v.label;model.predict(v[features])
    assert np.array_equal(snapshot[0],model['fill'].statistics_) and np.array_equal(snapshot[1],model['classifier'].centroids_)
    passed('unknown_label_not_negative_and_validation_never_refit')
    pp,align,inspect=ns['predict_pairs'],ns['align_predictions'],ns['inspect_archive']
    A,B=ns['A'],ns['B'];idsA,idsB=ns['order_A'],ns['order_B'];pairsA,pairsB=ns['pairs_A'],ns['pairs_B']
    permutations=0
    for ai in itertools.permutations(range(3)):
        for bi in itertools.permutations(range(2)):
            pa=pp(model,A.iloc[list(ai)]);pb=pp(model,B.iloc[list(bi)])
            assert align(idsA,pa)==[-1,1,-1] and align(idsB,pb)==[-1,1]
            assert dict(pa)==dict(pairsA) and dict(pb)==dict(pairsB)
            permutations+=1
    assert pp(model,A[['color','row_id','texture']])==pairsA
    assert pp(model,A.assign(label=[-1,1,1],later_report=[1,-1,1]))==pairsA
    passed('joint_row_permutations_and_named_feature_whitelist',permutations=permutations)
    absent_values=[None,np.nan,pd.NA,'','  ']; absent_cases=0
    for absent in absent_values:
        for fn in [lambda x=absent:align([x],[(x,1)]),lambda x=absent:align(['ok'],[(x,1)]),lambda x=absent:align([x],[('ok',1)])]:reject(fn);absent_cases+=1
        frame=A.copy();frame['row_id']=frame.row_id.astype(object);frame.loc[0,'row_id']=absent
        reject(lambda frame=frame:pp(model,frame));absent_cases+=1
    assert align(['abc'],[('abc',1)])==[1] and align([7],[(7,-1)])==[-1]
    badcases=[lambda:pp(model,A.drop(columns='color')),lambda:pp(model,pd.concat([A,A.iloc[:1]])),lambda:pp(model,A.assign(texture=[np.inf,1,4])),lambda:pp(model,A.assign(texture=['bad',1,4])),lambda:align(idsA,pairsA[:-1]),lambda:align(idsA,pairsA+[pairsA[0]]),lambda:align(idsA+[idsA[0]],pairsA)]
    for fn in badcases:reject(fn)
    for invalid in [0,True,np.bool_(False),1.0,'1',np.nan,np.inf,[1]]:
        reject(lambda invalid=invalid:align(['only'],[('only',invalid)]))
    passed('missing_id_helper_and_actual_path_plus_shape_value_guards',missing_id_cases=absent_cases,other_cases=len(badcases)+8)
    blob=ns['archive_bytes']
    with zipfile.ZipFile(io.BytesIO(blob)) as archive:
        assert archive.namelist()==['submissionA.csv','submissionB.csv']
        assert archive.read('submissionA.csv')==b'-1\n1\n-1\n'
        assert archive.read('submissionB.csv')==b'-1\n1\n'
    def independent_zip(entries):
        data=io.BytesIO()
        with zipfile.ZipFile(data,'w') as z:
            for key,value in entries:z.writestr(key,value)
        return data.getvalue()
    correctA='-1\n1\n-1\n';correctB='-1\n1\n'
    invalid_archives={
        'same_length_wrong_order':[('submissionA.csv','1\n-1\n-1\n'),('submissionB.csv',correctB)],
        'header':[('submissionA.csv','label\n'+correctA),('submissionB.csv',correctB)],
        'index_or_extra_column':[('submissionA.csv','0,-1\n1,1\n2,-1\n'),('submissionB.csv',correctB)],
        'missing_row':[('submissionA.csv','-1\n1\n'),('submissionB.csv',correctB)],
        'extra_row':[('submissionA.csv',correctA+'1\n'),('submissionB.csv',correctB)],
        'unknown_output':[('submissionA.csv','0\n1\n-1\n'),('submissionB.csv',correctB)],
        'probability_output':[('submissionA.csv','0.2\n1\n-1\n'),('submissionB.csv',correctB)],
        'wrong_filename':[('A.csv',correctA),('submissionB.csv',correctB)],
        'extra_member':[('submissionA.csv',correctA),('submissionB.csv',correctB),('readme','x')],
        'duplicate_member':[('submissionA.csv',correctA),('submissionA.csv',correctA)]}
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        errors={name:reject(lambda entries=entries:inspect(independent_zip(entries),idsA,pairsA,idsB,pairsB)) for name,entries in invalid_archives.items()}
    errors['not_zip']=reject(lambda:inspect(b'not a zip',idsA,pairsA,idsB,pairsB))
    # A format-valid constant baseline is possible; the formatter does not prove model quality.
    constA=[(x,-1) for x in idsA];constB=[(x,-1) for x in idsB]
    constblob=ns['make_archive'](idsA,constA,idsB,constB)
    assert inspect(constblob,idsA,constA,idsB,constB)=={'submissionA.csv':[-1,-1,-1],'submissionB.csv':[-1,-1]}
    corruptA=[(x,-label) for x,label in pairsA]
    corruptblob=ns['make_archive'](idsA,corruptA,idsB,pairsB)
    inspect(corruptblob,idsA,corruptA,idsB,pairsB)
    assert dict(corruptA)!=dict(pp(model,A))
    passed('independent_archive_parser_errors_and_formatter_scope',rejected=errors,constant_format_valid=True,corrupt_upstream_mapping_detected_by_model_oracle=True,formatter_alone_cannot_detect_upstream_corruption=True)
    excols=['vibration','sound','heat'];train=ns['exercise_train'];known=train[train.label.isin([0,1])];valid=ns['exercise_validation'];query=ns['exercise_input']
    exmeans,excenters,expred=manual_fit(known[excols].values.tolist(),known.label.tolist())
    assert [float(v) for v in exmeans]==[4,4,2]
    assert {str(k):[float(v) for v in vals] for k,vals in excenters.items()}=={'0':[1,3,1],'1':[7,5,3]}
    alternatives=[]
    for name,classifier in [('nearest_centroid',NearestCentroid()),('gaussian_naive_bayes',GaussianNB())]:
        fitted=make_model(classifier).fit(known[excols],known.label)
        pv=fitted.predict(valid[excols]).tolist();pq=fitted.predict(query[excols]).tolist()
        assert np.allclose(fitted['fill'].statistics_,[4,4,2]) and set(pq)<=set([0,1])
        if name=='nearest_centroid':assert pv==[expred(r) for r in valid[excols].values.tolist()]==[0,1,1] and pq==[1,0,0]
        else:assert hasattr(fitted['classifier'],'theta_') and hasattr(fitted['classifier'],'var_')
        with tempfile.TemporaryDirectory(prefix='independent-audit-') as directory:
            path=Path(directory)/'audit.csv';pd.DataFrame({'item':query.item,'signal':pq}).to_csv(path,index=False,lineterminator='\n')
            parsed=pd.read_csv(path);raw=path.read_text()
            assert parsed.columns.tolist()==['item','signal'] and parsed.item.tolist()==['J3','J1','J2'] and len(parsed)==3 and set(parsed.signal)<={0,1}
            assert raw.startswith('item,signal\n')
        alternatives.append(dict(model=name,validation_predictions=pv,accuracy=sum(a==b for a,b in zip(pv,valid.label))/3,input_predictions=pq,physical_audit_csv_reopened=True))
    assert alternatives[0]['validation_predictions']!=alternatives[1]['validation_predictions']
    passed('independent_new_contract_two_trained_models_and_real_csv',means=[4,4,2],known_ids=known.item.tolist(),unknown_ids=train.loc[train.label==-1,'item'].tolist(),models=alternatives)
    # Deliberate source changes. Successful execution is insufficient for some cases: own oracles are applied.
    mutants=[
      ('unknown_zero_relabelled_negative',3,'known_train = training[training["label"].isin([-1, 1])].copy()','known_train = training.copy(); known_train["label"] = known_train["label"].replace({0: -1})','notebook_assert'),
      ('target_in_features',3,'feature_cols = ["texture", "color"]','feature_cols = ["texture", "color", "label"]','notebook_assert'),
      ('train_and_validation_fit',5,'model.fit(known_train[feature_cols], known_train["label"])','model.fit(pd.concat([known_train[feature_cols], pd.DataFrame([[2000,3]],columns=feature_cols)]), pd.concat([known_train["label"],pd.Series([-1])]))','notebook_assert'),
      ('constant_imputation',5,'SimpleImputer(strategy="mean")','SimpleImputer(strategy="constant", fill_value=0)','notebook_assert'),
      ('training_target_reversed',5,'model.fit(known_train[feature_cols], known_train["label"])','model.fit(known_train[feature_cols], -known_train["label"])','notebook_assert'),
      ('validation_refit',11,'_ = model.predict(changed_validation[feature_cols])','model.fit(changed_validation[feature_cols], changed_validation["label"]); _ = model.predict(changed_validation[feature_cols])','notebook_assert'),
      ('positional_prediction_order',15,'return [mapping[row_id] for row_id in ids]','return [label for _, label in pairs]','notebook_assert'),
      ('missing_id_guard_bypassed',15,'if any(is_missing_id(row_id) for row_id in ids):','if False:','notebook_assert'),
      ('boolean_output_allowed',15,'if isinstance(prediction, (bool, np.bool_)) or not isinstance(prediction, (int, np.integer)):','if not isinstance(prediction, (int, np.integer)):','independent_bool_oracle'),
      ('unknown_zero_output_allowed',15,'if int(prediction) not in (-1, 1):','if int(prediction) not in (-1, 0, 1):','notebook_assert'),
      ('forbidden_header_added',17,'writer.writerows([[value] for value in labels])','writer.writerow(["label"]); writer.writerows([[value] for value in labels])','notebook_assert'),
      ('wrong_zip_filename',17,'archive.writestr("submissionA.csv", text_A)','archive.writestr("A.csv", text_A)','notebook_assert'),
      ('physical_zip_replaced_by_memory',19,'practice_zip.write_bytes(archive_bytes)\n    read_back = practice_zip.read_bytes()','read_back = archive_bytes','independent_physical_io_oracle')]
    mutation_results=[]
    for name,index,old,new,detector in mutants:
        variant=copy.deepcopy(book);assert variant.cells[index].source.count(old)==1,(name,'replacement mismatch');variant.cells[index].source=variant.cells[index].source.replace(old,new)
        if name=='missing_id_guard_bypassed':
            variant.cells[index].source=variant.cells[index].source.replace('if is_missing_id(row_id):','if False:')
        variant_dir=OUT/'mutation-inputs';variant_dir.mkdir(exist_ok=True)
        variant_path=variant_dir/(name+'.ipynb');nbformat.write(variant,variant_path)
        process=subprocess.run([sys.executable,'-B',str(Path(__file__)),'--worker',str(variant_path),detector],capture_output=True,text=True,timeout=90)
        assert process.returncode==0,(name,process.stderr)
        output=json.loads(process.stdout)
        failure=output['evidence']
        assert output['detected'],name+' survived'
        assert 'AttributeError' not in failure and 'NoneType' not in failure,'harness failure, not valid detection: '+failure
        if failure.startswith('cell '):
            failing_cell=int(failure.split(':')[0].split()[1])
            assert failing_cell>=index,(name,'failed before mutation',failure)
        mutation_results.append(dict(name=name,source_cell=index,old=old,new=new,additional_change='prediction ID guard also disabled' if name=='missing_id_guard_bypassed' else None,detector=detector,status='detected',evidence=failure,fresh_process=True))
    passed('source_mutation_tests',count=len(mutation_results),results=mutation_results)
    (OUT/'mutation-results.json').write_text(json.dumps(mutation_results,ensure_ascii=False,indent=2)+'\n')
    # Preserved inputs and the link-only extension have different claims from previous full-artifact reviews.
    manifest=json.loads((OUT/'input-manifest-v1.json').read_text());unchanged=[]
    for row in manifest['files']:
        if 'week01_axes_linear_bridge' in row['path']:continue
        assert sha(ROOT/row['path'])==row['sha256'],row['path']+' changed'
        unchanged.append(row['path'])
    bridge=ROOT/'lessons/week01/week01_axes_linear_bridge.ipynb'
    old=json.loads(subprocess.check_output(['git','show',manifest['git_head']+':lessons/week01/week01_axes_linear_bridge.ipynb'],cwd=ROOT))
    current=json.loads(bridge.read_text());assert len(old['cells'])==len(current['cells'])
    diffs=[]
    for i,(a,b) in enumerate(zip(old['cells'],current['cells'])):
        if a!=b:
            assert a['cell_type']==b['cell_type']=='markdown'
            oldsource=''.join(a['source']);newsource=''.join(b['source'])
            addition='\n\n다음으로 [낯선 문제를 읽고 예측까지](week01_problem_pipeline.ipynb)에서 문제 해석 → 전처리 → 모델 fit → 검증 → 제출 형식을 연결합니다.\n'
            diffs.append(dict(cell=i,before=oldsource,after=newsource))
    assert len(diffs)==1 and 'week01_problem_pipeline.ipynb' in diffs[0]['after']
    assert all(a==b for a,b in zip(old['cells'],current['cells']) if a['cell_type']=='code')
    for path in [NB,bridge]:
        html,_=HTMLExporter().from_notebook_node(nbformat.read(path,as_version=4))
        assert html==path.with_suffix('.html').read_text()
    passed('frozen_input_hashes_and_bridge_link_only',unchanged_files=unchanged,bridge_changed_markdown=diffs,code_and_outputs_equal_frozen_git_head=True,html_fresh_export_equal=True)
    text='\n'.join(c.source for c in book.cells)
    forbidden=['120분','5~7시간','교사는 독립 수행 전에','실측','수업 시간','자습 시간','운영 계획','분량 조절']
    assert not any(term in text for term in forbidden)
    passed('student_timing_internal_ops_absent',searched_terms=forbidden,learning_instructions_and_prediction_time_preserved=True)
    assert before=={str(p.relative_to(ROOT)):sha(p) for p in tracked}
    result=dict(checked_at_utc=datetime.now(timezone.utc).isoformat(),source_sha256=before,script_sha256=sha(Path(__file__)),criteria_sha256=sha(OUT/'criteria-v1.md'),criteria_addendum_sha256=sha(OUT/'criteria-addendum-01.md'),execution='fresh InProcessKernelManager; no socket kernel; all 12 code cells including blank answer executed sequentially',environment=dict(python=sys.version.split()[0],numpy=np.__version__,pandas=pd.__version__,sklearn=sklearn.__version__),checks=checks,blocking_defects=[],limits=['Finite synthetic checks only; no official Antique data, server submission or 2027 contest question attempted','Student answer cell is blank; no actual student independent work or mastery observed','Total student workload and 120-minute feasibility unmeasured; supplements may increase burden','Normal socket Jupyter/Colab and full browser visual rendering unverified','Public teacher notes are not access control; protected hidden final tests not generated or executed','Formatter can check consistency with a mapping, not whether the upstream mapping is true'])
    (OUT/'validation-results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(source_sha256=EXPECTED,checks=len(checks),mutations=len(mutants),blocking_defects=[],alternatives=alternatives),ensure_ascii=False,indent=2))
finally:
    shutil.rmtree(RUNTIME,ignore_errors=True)
