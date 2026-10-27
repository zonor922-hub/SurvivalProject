"""Expected rejections in an unsaved external Blueprint, including private helpers."""
import pathlib,sys,json,traceback,time
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from inventory_graph_helpers import *
r={'tests':[]}
try:
    bp=unreal.load_asset('/Game/Survival/Inventory/BPC_Inventory');assert B.compile_blueprint(bp)
    external=B.create_blueprint_asset_with_parent('/Game/__InventoryContractTests/External'+str(time.time_ns()),unreal.Object)
    for kind,names in [('setter',('Slots','Revision','InventoryId','MaxWeight','Initialized','CatalogGameInstance','MutationInProgress')),('helper',('SimulateAddExact','SimulateRemoveExact','ValidateSlots','CommitInventory'))]:
        for name in names:
            ed=graph(external,'Attempt');target=ed.add_graph_input_parameter('Target',B.get_object_reference_type(bp.generated_class()))
            n=ed.add_set_member_variable_node(name,bp.generated_class().get_path_name()) if kind=='setter' else call(ed,own(bp,name))
            if n:
                wire(target,pin(n,'self'));wire(ed.find_graph_entry_pin(),pin(n,'execute'));B.compile_blueprint(external)
                rejected='BS_ERROR' in str(external.get_editor_property('status'))
            else:rejected=True
            r['tests'].append({'test':'external '+kind+' rejected '+name,'passed':rejected});assert rejected,name
            B.remove_function_graph(external,'Attempt');assert B.compile_blueprint(external)
    for name in ('TryAddExact','TryRemoveExact'):
        ed=graph(external,'PublicCall');target=ed.add_graph_input_parameter('Target',B.get_object_reference_type(bp.generated_class()));n=call(ed,own(bp,name));wire(target,pin(n,'self'));wire(ed.find_graph_entry_pin(),pin(n,'execute'));assert B.compile_blueprint(external)
        r['tests'].append({'test':'public command compiles '+name,'passed':True});B.remove_function_graph(external,'PublicCall')
    r['passed']=True
except Exception:r['error']=traceback.format_exc();r['passed']=False
pathlib.Path(__file__).with_name('a09_access_verification.json').write_text(json.dumps(r,indent=2),encoding='utf-8')
assert r['passed'],r.get('error')
