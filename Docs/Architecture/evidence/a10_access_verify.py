"""A10 public signatures and private lookup compile contract, unsaved external BP."""
import unreal,pathlib,json,traceback,time
from inventory_graph_helpers import *
r={'tests':[]}
try:
    bp=unreal.load_asset('/Game/Survival/Inventory/BPC_Inventory')
    external=B.create_blueprint_asset_with_parent('/Game/__InventoryContractTests/A10Access'+str(time.time_ns()),unreal.Object)
    for name,private in [('FindStackIndex',True),('TrySplit',False),('TryMerge',False)]:
        ed=graph(external,'Attempt');target=ed.add_graph_input_parameter('Inventory',B.get_object_reference_type(bp.generated_class()));n=call(ed,own(bp,name))
        wire(target,pin(n,'self'));wire(ed.find_graph_entry_pin(),pin(n,'execute'));B.compile_blueprint(external)
        status=external.get_editor_property('status');ok=status==(unreal.BlueprintStatus.BS_ERROR if private else unreal.BlueprintStatus.BS_UP_TO_DATE)
        r['tests'].append({'test':name+(' private rejected' if private else ' public callable'),'passed':ok,'status':str(status)});assert ok,name
        B.remove_function_graph(external,'Attempt');assert B.compile_blueprint(external)
    r['passed']=True
except Exception:r['passed']=False;r['error']=traceback.format_exc()
pathlib.Path(__file__).with_name('a10_access_verification.json').write_text(json.dumps(r,indent=2),encoding='utf-8')
assert r['passed'],r.get('error')
