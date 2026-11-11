from pathlib import Path
import ast
import copy
import hashlib
import unittest
import numpy as np
import nbformat
from sklearn.dummy import DummyClassifier
from sklearn.metrics import precision_recall_fscore_support

ROOT=Path(__file__).resolve().parents[3]
NOTEBOOK=ROOT/'lessons/week02/week02_temporal_preprocessing.ipynb'
if not NOTEBOOK.exists(): raise RuntimeError('missing notebook')
nb=nbformat.read(NOTEBOOK,4)
cell=next(c for c in nb.cells if c.id=='w02-known-mode')
module=ast.parse(cell.source)
function=next(x for x in module.body if isinstance(x,ast.FunctionDef) and x.name=='fit_known_mode')
namespace={'np':np,'DummyClassifier':DummyClassifier}
exec(compile(ast.Module(body=[function],type_ignores=[]),str(NOTEBOOK),'exec'),namespace)
fit=namespace['fit_known_mode']
weighted_cell=next(c for c in nb.cells if c.id=='e12109a7')
weighted_ast=ast.parse(weighted_cell.source)
weighted_fn=next(x for x in weighted_ast.body if isinstance(x,ast.FunctionDef) and x.name=='weighted_accuracy')
exec(compile(ast.Module(body=[weighted_fn],type_ignores=[]),str(NOTEBOOK),'exec'),namespace)
weighted=namespace['weighted_accuracy']

class KnownModeTests(unittest.TestCase):
    def test_worked_known_b_despite_unknown_majority(self):
        model,chosen,mask=fit(['B','B','B','T',0,0,0,0,0])
        self.assertEqual(chosen,'B')
        self.assertEqual(mask.tolist(),[True]*4+[False]*5)
        self.assertEqual(model.predict(np.arange(6).reshape(-1,1)).tolist(),['B']*6)
        self.assertEqual(model.class_prior_.tolist(),[0.75,0.25])
    def test_independent_reverse_and_order(self):
        model,chosen,mask=fit(['B','T','T','T',0,0,0,0])
        self.assertEqual(chosen,'T')
        self.assertEqual(mask.tolist(),[True]*4+[False]*4)
        self.assertEqual(model.predict(np.arange(8).reshape(-1,1)).tolist(),['T']*8)
        self.assertEqual(model.class_prior_.tolist(),[0.25,0.75])
    def test_reverse_training_only_on_refit(self):
        first,_,_=fit(['B','T','T','T',0,0,0,0])
        second,_,_=fit(['T','B','B','B',0,0,0,0])
        x=np.array([[30],[10],[20]])
        self.assertEqual(first.predict(x).tolist(),['T']*3)
        self.assertEqual(second.predict(x).tolist(),['B']*3)
        self.assertEqual(first.predict(x).tolist(),['T']*3)
    def test_validation_labels_do_not_change_fitted_state_or_predictions(self):
        model,_,_=fit(['B','T','T','T',0,0,0,0])
        x=np.array([[99],[10],[33],[5],[1],[0],[11],[6]])
        pred=model.predict(x).copy(); state=copy.deepcopy(model.__dict__)
        original=np.array(['B']*6+['T']*2)
        changed=np.array(['T']*6+['B']*2)
        self.assertNotEqual(float((pred==original).mean()),float((pred==changed).mean()))
        self.assertTrue(np.array_equal(model.predict(x),pred))
        for key,old in state.items():
            now=model.__dict__[key]
            if isinstance(old,np.ndarray): np.testing.assert_array_equal(now,old)
            else: self.assertEqual(now,old)
    def test_features_do_not_change_prediction(self):
        model,_,_=fit(['B','B','B','T',0])
        self.assertEqual(model.predict([[1],[99],[-2]]).tolist(),['B']*3)
    def test_tie_stops(self):
        with self.assertRaisesRegex(ValueError,'동률'): fit(['B','T',0,0])
    def test_no_known_stops(self):
        with self.assertRaisesRegex(ValueError,'없습니다'): fit([0,0.0])
        with self.assertRaisesRegex(ValueError,'없습니다'): fit([])
    def test_boolean_is_not_unknown(self):
        for bad in [False,True,np.bool_(False),np.bool_(True)]:
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError): fit(['B','B','T',bad])
    def test_numeric_float_zero_is_unknown(self):
        model,chosen,mask=fit(['B','B','T',0.0])
        self.assertEqual(chosen,'B');self.assertEqual(mask.tolist(),[True,True,True,False])
    def test_invalid_label_stops(self):
        for bad in ['unknown',None,1,-1,np.nan]:
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError): fit(['B','B','T',bad])
    def test_single_known_class_is_fittable_but_other_class_absent(self):
        model,chosen,_=fit(['T',0,0.0])
        self.assertEqual(chosen,'T')
        self.assertEqual(model.classes_.tolist(),['T'])
        self.assertEqual(model.predict([[42]]).tolist(),['T'])
        self.assertEqual(model.predict_proba([[42]]).shape,(1,len(model.classes_)))
    def test_worked_validation_metrics(self):
        model,_,_=fit(['B','B','B','T',0,0,0,0,0])
        actual=np.array(['B']*5+['T']); a=model.predict(np.arange(6).reshape(-1,1))
        b=np.array(['B','B','B','T','T','T'])
        p,r,f,_=precision_recall_fscore_support(actual,a,average='binary',pos_label='T',zero_division=np.nan)
        self.assertTrue(np.isnan(p));self.assertEqual((r,f),(0,0))
        self.assertEqual(precision_recall_fscore_support(actual,a,average='binary',pos_label='T',zero_division=0)[0],0)
        self.assertAlmostEqual(weighted(actual,a,5),0.5)
        self.assertAlmostEqual(weighted(actual,b,5),0.8)
        self.assertEqual(precision_recall_fscore_support(actual,b,average='binary',pos_label='T',zero_division=0)[:3],(1/3,1,0.5))
    def test_independent_metrics_and_selection(self):
        model,_,_=fit(['B','T','T','T',0,0,0,0])
        actual=np.array(['B']*6+['T']*2)
        candidates={'mode':model.predict(np.arange(8).reshape(-1,1)), 'U':np.array(['B']*8), 'V':np.array(['B']*3+['T']*5)}
        expected={'mode':(1/4,1/4,1,2/5,4/7),'U':(3/4,np.nan,0,0,3/7),'V':(5/8,2/5,1,4/7,11/14)}
        values={}
        for name,pred in candidates.items():
            precision,recall,f1,_=precision_recall_fscore_support(actual,pred,average='binary',pos_label='T',zero_division=np.nan)
            values[name]=((actual==pred).mean(),precision,recall,f1,weighted(actual,pred,4))
            np.testing.assert_allclose(values[name],expected[name],rtol=0,atol=1e-12,equal_nan=True)
        self.assertEqual(max(values,key=lambda k: values[k][0]),'U')
        self.assertEqual({k for k,v in values.items() if v[2]==max(x[2] for x in values.values())},{'mode','V'})
        self.assertEqual(max(values,key=lambda k: values[k][4]),'V')

if __name__=='__main__':
    print('Target SHA256',hashlib.sha256(NOTEBOOK.read_bytes()).hexdigest(),flush=True)
    unittest.main(verbosity=2)
