"""Read-only asset probe for the A09/A11 inactive-durability contract conflict."""
import unreal,pathlib,sys,json,traceback,hashlib
root=pathlib.Path('D:/Project/SurvivalProject_A11');sys.path.insert(0,str(root/'Docs/Architecture/evidence'))
from inventory_graph_helpers import *
from a09_verify import read,write,snapshot,items,result
from inventory_event_fixture import listener_class
out=root/'Saved/Verification/A11';r={'engine':unreal.SystemLibrary.get_engine_version(),'project':unreal.Paths.project_dir(),'passed':False};bp=None
asset=root/'Content/Survival/Inventory/BPC_Inventory.uasset';r['sha256_before']=hashlib.sha256(asset.read_bytes()).hexdigest()
try:
 bp=unreal.load_asset('/Game/Survival/Inventory/BPC_Inventory');gi=unreal.new_object(unreal.load_asset('/Game/Survival/Core/BP_SurvivalGameInstance').generated_class());gi.call_method('InitializeCatalog')
 ed=graph(bp,'A11ProbeSlots');v=ed.add_graph_input_parameter('Value',B.get_array_type(type_asset('FInventorySlot')));member(ed,'Slots',v,ed.find_graph_entry_pin());assert B.compile_blueprint(bp)
 def new(q,dur):
  o=unreal.new_object(bp.generated_class());o.call_method('InitializeInventory',(gi,4,100.));slots=list(read(snapshot(o),'Slots'));s=read(slots[0],'ItemStack');write(s,'ItemId','item.wood');write(s,'Quantity',q);assert result(o.call_method('TryAddExact',(s,)))[0];slots=list(read(snapshot(o),'Slots'));s=read(slots[0],'ItemStack');write(s,'Durability',dur);write(slots[0],'ItemStack',s);o.call_method('A11ProbeSlots',(slots,));return o
 control=new(5,80.);source=new(10,37.);destination=new(5,80.);taken=read(items(source)[0],'StackId')
 request=read(items(source)[0],'Quantity');s=items(source)[0];write(s,'Quantity',3)
 cb=snapshot(control).export_text();a09=result(control.call_method('TryAddExact',(s,)));r['a09']={'before':cb,'result':a09,'after':snapshot(control).export_text(),'destination_durability_after':read(items(control)[0],'Durability')}
 before=[snapshot(o).export_text() for o in [source,destination]]
 lbp=listener_class(bp);listeners=[unreal.new_object(lbp.generated_class()) for _ in range(2)]
 for listener,o in zip(listeners,[source,destination]):listener.call_method('BindInventory',(o,))
 raw=source.call_method('TryTransferExact',(destination,taken,3,1,1));after=[snapshot(o).export_text() for o in [source,destination]]
 r['a11']={'before':before,'result':result(raw[0]),'destination_new_revision':raw[1],'after':after,'snapshots_unchanged':before==after,'events':[x.get_editor_property('EventCount') for x in listeners],'guards':[o.get_editor_property('MutationInProgress') for o in [source,destination]]}
 # Prove SimulateAddExact was not touched by the limited A09 refactor.
 P=unreal.BlueprintGraphPinLibrary;nodes=[];ed=G.get_graph_editor_by_name(bp,'SimulateAddExact')
 for n in ed.list_all_nodes():
  row={'name':n.get_name(),'class':n.get_class().get_name(),'title':str(B.get_node_title(n)),'pins':[]}
  for p in B.list_all_pins(n):row['pins'].append({'name':str(P.get_pin_name(p)),'direction':str(P.get_pin_direction(p)),'get_pin_value':str(P.get_pin_value(p)),'connections':[{'node':P.get_owning_node(q).get_name(),'pin':str(P.get_pin_name(q))} for q in P.list_connected_pins(p)]})
  nodes.append(row)
 original=json.loads((root/'Docs/Architecture/evidence/a11_blocker_inspection.json').read_text(encoding='utf-8'))['graphs']['SimulateAddExact']
 r['simulate_add_graph_unchanged']=nodes==original
 r['merge_make_struct']=[n for n in nodes if n['name']=='K2Node_MakeStruct_0']
 r['conflict_confirmed']=a09[:3]==(True,1,3) and r['a09']['destination_durability_after']==37. and r['a11']['result']==(False,0,0,1) and r['a11']['snapshots_unchanged'] and r['a11']['events']==[0,0] and r['a11']['guards']==[False,False] and r['simulate_add_graph_unchanged']
 r['passed']=r['conflict_confirmed']
except Exception:r['error']=traceback.format_exc()
finally:
 if bp:
  B.remove_function_graph(bp,'A11ProbeSlots');r['cleanup_compile']=B.compile_blueprint(bp);r['status']=str(bp.get_editor_property('status'))
 r['sha256_after']=hashlib.sha256(asset.read_bytes()).hexdigest();r['passed']=r['passed'] and r['sha256_before']==r['sha256_after'] and r.get('cleanup_compile',False)
(out/'inactive_durability_conflict.json').write_text(json.dumps(r,indent=2,ensure_ascii=False),encoding='utf-8');unreal.SystemLibrary.quit_editor()
