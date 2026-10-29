"""Private A11 helpers rejected specifically by access control, public command callable."""
import unreal,pathlib,json,time,traceback
from inventory_graph_helpers import *
r={'tests':[],'passed':False};external=None
try:
 bp=unreal.load_asset('/Game/Survival/Inventory/BPC_Inventory');external=B.create_blueprint_asset_with_parent('/Game/__InventoryContractTests/A11Access'+str(time.time_ns()),unreal.Object)
 for name,private in [(n,True) for n in ['SimulateTakeStack','SimulateReceiveStack','ApplyCandidate','BroadcastChange','FindStackIndex','CheckTransferInvariants','CheckStackIdsUnique','CheckReceiveExact']]+[('TryTransferExact',False)]:
  ed=graph(external,'Attempt');target=ed.add_graph_input_parameter('Inventory',B.get_object_reference_type(bp.generated_class()));n=call(ed,own(bp,name));feed(n,'self',target);wire(ed.find_graph_entry_pin(),pin(n,'execute'));B.compile_blueprint(external)
  status=external.get_editor_property('status');messages=[str(x.get_editor_property('error_msg')) for x in ed.list_all_nodes() if str(x.get_editor_property('error_msg'))]
  ok=(status==unreal.BlueprintStatus.BS_ERROR and any('частн' in x.lower() or 'private' in x.lower() for x in messages)) if private else status==unreal.BlueprintStatus.BS_UP_TO_DATE
  r['tests'].append({'test':name,'passed':ok,'status':str(status),'messages':messages});assert ok,(name,messages)
  B.remove_function_graph(external,'Attempt');assert B.compile_blueprint(external)
 r['passed']=True
except Exception:r['error']=traceback.format_exc()
finally:
 if external:B.remove_function_graph(external,'Attempt');B.compile_blueprint(external)
pathlib.Path(__file__).with_name('a11_access_verification.json').write_text(json.dumps(r,indent=2,ensure_ascii=False),encoding='utf-8');assert r['passed'],r.get('error')
