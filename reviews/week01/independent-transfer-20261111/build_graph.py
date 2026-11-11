"""Bind explicit scoped teaching routes to current local artifact bytes; no semantic acceptance."""
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'tools'))
import graph_paths
out=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
book='lessons/week01/week01_python_tables.ipynb'; key='lessons/week01/teacher-notes.txt'; brief=str((out/'source-brief.md').relative_to(ROOT))
# Locators are declarations: reviewers must inspect the actual associated content.
topics=[
 ('traceback','Python 오류 위치와 수정','예시 1: 함수 호출의 상태와 출력','cell:7208718e','cell:e594ea69 + cell:7208718e','cell:7208718e','cell:7208718e + cell:ab8d9d90','Python 진단과 실제 수정 과제: traceback 진단'),
 ('chart','새 표의 좌표 구성·이동과 인과 한계','예시 3: 연속 변수 관계·분포의 시각화 선택','cell:fa10c459','cell:b5362bd2','cell:48d931b0','cell:d60c3acd + cell:dff8752b','새 입력 학습 확인 답: 새 그래프'),
 ('broadcast','새 배열의 축·보정 shape 선택','예시 2: shape·축·메모리; 서술형 2: KNN 거리 broadcasting 권장','cell:e594ea69','cell:0caaa0ca','cell:053a193f','cell:df2802a3','수업 밖 필수 연습 해설: 새 브로드캐스팅'),
 ('variance','새 값의 분산·이동·배율 설명','예시 24: 피처 엔지니어링 기법 판별','cell:82e8a039','cell:9ce91662 + cell:guided-feedback-and-support','cell:ea9aba74','cell:9ce91662 + cell:variance-independent-response','수업 밖 필수 연습 해설: 새 독립 분산'),
 ('merge','없는 키와 중복 키의 병합 결과','예시 서술형 2: KNN 입출력·다수결 계약','cell:876b91b7','cell:0fd965eb','cell:0fd965eb + cell:02c6cde1','cell:0fd965eb, 소제목 새 병합 조건을 먼저 예측하기 + cell:13559279','수업 밖 필수 연습 해설: 병합 경계'),
]
roles=graph_paths.ROLES;g={'nodes':[],'edges':[]};spec={'schema_version':1,'synthetic':False,'required_demands':[],'paths':[]}
for name,label,demand,prereq,theory,practice,assessment,feedback in topics:
 ids={role:f'{name}:{role}' for role in roles}
 for role in roles:g['nodes'].append({'id':ids[role],'type':'evidence','status':'completed','label':demand if role=='demand' else label+' / '+role})
 g['nodes'].append({'id':name+':local-goal','type':'request','status':'completed','label':'1주차 기초 목표: '+label})
 for a,b in zip(roles,roles[1:]):
  g['edges'].append({'from':ids[a],'to':ids[b],'type':'informs' if a=='demand' else 'supports','note':'교육적 선수관계 추론; 공식 문제와 동일 과제가 아님' if a=='demand' else 'Recorded relationship; semantic meaning requires review.'})
 g['edges'].append({'from':ids['demand'],'to':name+':local-goal','type':'informs','note':'Staged instructional inference, not a direct official requirement.'})
 g['edges'].append({'from':name+':local-goal','to':ids['independent_assessment'],'type':'informs'})
 g['edges'].append({'from':ids['feedback'],'to':ids['coding_practice'],'type':'informs','note':'Proposed retry after feedback; no learner retry is claimed.'})
 spec['required_demands'].append(ids['demand'])
 entries={}
 for role,path,loc in [('source',brief,'KOAI 2027, linked syllabus and 2026 example status'),('demand',brief,'공식 요구와 1주차 목표의 구분 표: '+name+' 행'),('prerequisite',book,prereq),('theory_explanation',book,theory),('coding_practice',book,practice),('independent_assessment',book,assessment),('feedback',key,feedback)]:
  entries[role]={'path':path,'sha256':sha(path),'locator':loc,'revision':'week1-independent-transfer-v2','origin':'Direct source brief or exact current notebook/teacher notes; claims not authenticated by hashes.'}
 spec['paths'].append({'id':'path:'+name,'comparison_id':name,'roles':ids,'provenance':entries,
  'assessment':{'independent':True,'answer_conditions':'Hide worked examples and teacher key before first answer; record actual help.','allowed_support':'Learner may use hints or examples and records assistance; actual independence remains unobserved.'}})
for name,obj in [('graph.json',g),('paths.json',spec)]: (out/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
r=graph_paths.inspect_paths(g,spec,ROOT);(out/'graph-validation.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'mechanical':r['status'],'paths':len(r['paths']),'source_authenticity':r['verification']['source_authenticity']}))
