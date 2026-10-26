"""Expected compiler rejection in an unsaved external test Blueprint; never save it."""
import pathlib,sys,json,traceback
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from a08_bp_helpers import *
r={'tests':[]}
try:
 bp=unreal.load_asset('/Game/Survival/Inventory/BPC_Inventory');assert B.compile_blueprint(bp)
 external=B.create_blueprint_asset_with_parent('/Game/__A08AccessTest/External',unreal.Actor)
 for name in ('Slots','Revision','InventoryId','MaxWeight','Initialized','CatalogGameInstance'):
  ed=graph(external,'AttemptSet');target=ed.add_graph_input_parameter('Target',B.get_object_reference_type(bp.generated_class()))
  node=ed.add_set_member_variable_node(name,bp.generated_class().get_path_name())
  if node:
   wire(target,pin(node,'self'));wire(ed.find_graph_entry_pin(),pin(node,'execute'));B.compile_blueprint(external)
   rejected='BS_ERROR' in str(external.get_editor_property('status'))
  else:rejected=True
  r['tests'].append({'test':'external setter rejected '+name,'passed':rejected});assert rejected,name
  B.remove_function_graph(external,'AttemptSet');assert B.compile_blueprint(external)
 ed=graph(external,'ReadPublicState');target=ed.add_graph_input_parameter('Target',B.get_object_reference_type(bp.generated_class()));ret=ed.add_graph_output_parameter('Ready',basic('bool'));wire(ed.find_graph_entry_pin(),pin(ret,'execute'))
 getter=call(ed,own(bp,'IsInitialized'));wire(target,pin(getter,'self'));wire(pin(getter,'Ready'),pin(ret,'Ready'));assert B.compile_blueprint(external)
 r['tests'].append({'test':'external public readiness compiles','passed':True});r['passed']=True
except Exception:r['error']=traceback.format_exc();r['passed']=False
(pathlib.Path(__file__).resolve().with_name('a08_access_verification.json')).write_text(json.dumps(r,indent=2),encoding='utf-8')
assert r['passed'],r.get('error')
