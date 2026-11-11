"""No kernel: preserve stream metadata, display/execute barriers and ordering."""
from pathlib import Path
from types import SimpleNamespace
import copy
import importlib.util
import json

ROOT=Path(__file__).resolve().parents[3]
spec=importlib.util.spec_from_file_location("validator",ROOT/"lessons/week02/teacher_validate_week02.py")
module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
class Node(dict):
    def __getattr__(self,name):
        try: return self[name]
        except KeyError as exc: raise AttributeError(name) from exc
    def __setattr__(self,name,value): self[name]=value

def stream(text,name="stdout",**extra): return Node(output_type="stream",name=name,text=text,**extra)
def run(outputs):
    cell=Node(cell_type="code",outputs=copy.deepcopy(outputs))
    module.coalesce_stream_outputs(SimpleNamespace(cells=[cell]))
    return cell.outputs

a=stream("A"); b=stream("B"); display=Node(output_type="display_data",data={"text/plain":"display"},metadata={})
execute=Node(output_type="execute_result",execution_count=9,data={"text/plain":"result"},metadata={})
cases={
 "adjacent_identical_streams":run([a,b])==[stream("AB")],
 "display_barrier":run([a,display,b])==[a,display,b],
 "execute_result_barrier":run([a,execute,b])==[a,execute,b],
 "stderr_barrier":run([a,stream("error","stderr"),b])==[a,stream("error","stderr"),b],
 "different_stream_metadata_preserved":run([stream("A",metadata={"x":1}),stream("B",metadata={"x":2})])==[stream("A",metadata={"x":1}),stream("B",metadata={"x":2})],
 "same_stream_metadata_preserved":run([stream("A",metadata={"x":1}),stream("B",metadata={"x":1})])==[stream("AB",metadata={"x":1})],
 "different_extra_fields_preserved":run([stream("A",custom="first"),stream("B",custom="second")])==[stream("A",custom="first"),stream("B",custom="second")],
 "numeric_text_unchanged":''.join(o.text for o in run([stream("mean=4;"),stream("scale=1.4142135623730951")]))=="mean=4;scale=1.4142135623730951",
 "input_objects_not_modified":a==stream("A") and b==stream("B"),
}
report={"all_passed":all(cases.values()),"cases":cases,"rule":"only adjacent same-stream outputs whose non-text fields are equal; preserve all barriers and text"}
Path(__file__).with_name("stream-coalescing-results.json").write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
if not report["all_passed"]: raise SystemExit(1)
