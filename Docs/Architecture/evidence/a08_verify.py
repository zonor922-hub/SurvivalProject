"""A08 component contract tests; temporary fixture function is removed in finally."""
import unreal,json,pathlib,traceback,re,sys,time
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from a08_bp_helpers import *
r={'tests':[]};out=pathlib.Path(__file__).resolve().with_name('a08_verification.json');restore=None;seed_name=None
try:
 bp=unreal.load_asset('/Game/Survival/Inventory/BPC_Inventory');gi_bp=unreal.load_asset('/Game/Survival/Core/BP_SurvivalGameInstance');gi=unreal.new_object(gi_bp.generated_class());gi.call_method('InitializeCatalog');o=unreal.new_object(bp.generated_class())
 def check(label,cond,detail=''):
  r['tests'].append({'test':label,'passed':bool(cond),'detail':str(detail)});assert cond,label
 def field(obj,n):
  m=re.search(r'(?<!\w)('+re.escape(n)+r'_\d+_[A-F0-9]+)=',obj.export_text());assert m,(n,obj.export_text());return m.group(1)
 def read(obj,n):return obj.get_editor_property(field(obj,n))
 def write(obj,n,v):obj.set_editor_property(field(obj,n),v)
 check('uninitialized public readiness',not o.call_method('IsInitialized'))
 initial=o.call_method('GetSnapshot');check('uninitialized defaults empty and zero GUID',len(read(initial,'Slots'))==0 and not unreal.GuidLibrary.is_valid_guid(read(initial,'InventoryId')))
 check('uninitialized weight invalid',o.call_method('GetCurrentWeight')==(0.0,False))
 o.call_method('InitializeInventory',(gi,4,10.0));check('initialized',o.get_editor_property('Initialized'))
 snap=o.call_method('GetSnapshot');slots=read(snap,'Slots');check('four empty indexed slots',len(slots)==4 and all(read(s,'SlotIndex')==i and not read(s,'HasItem') for i,s in enumerate(slots)))
 check('empty weight zero',o.call_method('GetCurrentWeight')==(0.0,True));check('capacity and revision',read(snap,'MaxWeight')==10 and read(snap,'Revision')==0)
 identity=read(snap,'InventoryId');check('nonzero inventory GUID',unreal.GuidLibrary.is_valid_guid(identity))
 other=unreal.new_object(bp.generated_class());other.call_method('InitializeInventory',(gi,4,10.0));check('distinct inventories get unique GUIDs',read(other.call_method('GetSnapshot'),'InventoryId').export_text()!=identity.export_text())
 check('public readiness after init',o.call_method('IsInitialized'))
 # Mutating the returned value must never mutate component storage.
 copy_slots=list(slots);write(copy_slots[0],'HasItem',True);stack=read(copy_slots[0],'ItemStack');write(stack,'ItemId','item.wood');write(stack,'Quantity',2);write(stack,'StackId',unreal.GuidLibrary.new_guid());write(copy_slots[0],'ItemStack',stack);write(snap,'Slots',copy_slots)
 check('snapshot detached copy',not read(read(o.call_method('GetSnapshot'),'Slots')[0],'HasItem') and o.call_method('GetCurrentWeight')==(0.0,True))
 write(snap,'Revision',999);write(snap,'MaxWeight',999.0);check('snapshot metadata detached',read(o.call_method('GetSnapshot'),'Revision')==0 and read(o.call_method('GetSnapshot'),'MaxWeight')==10.0)
 seed_name='A08TestSeed'+str(time.time_ns());ed=graph(bp,seed_name);sp=ed.add_graph_input_parameter('SeedSlots',B.get_array_type(B.get_struct_type(unreal.load_asset('/Game/Survival/Items/Types/FInventorySlot'))));gp=ed.add_graph_input_parameter('SeedGameInstance',B.get_object_reference_type(gi_bp.generated_class()));ip=ed.add_graph_input_parameter('SeedInventoryId',B.get_struct_type(unreal.Guid.static_struct()))
 entry=ed.find_graph_entry_pin()
 for n,v in [('Slots',sp),('CatalogGameInstance',gp),('InventoryId',ip)]:
  node=setv(ed,n);wire(v,pin(node,n));wire(entry,pin(node,'execute'));entry=pin(node,'then')
 for n,v in [('Initialized','true'),('Revision','7'),('MaxWeight','10.0')]:
  node=setv(ed,n,v);wire(entry,pin(node,'execute'));entry=pin(node,'then')
 assert B.compile_blueprint(bp)
 def seeded(values):
  obj=unreal.new_object(bp.generated_class());obj.call_method(seed_name,(values,gi,identity));return obj
 fixture=seeded(copy_slots);check('derived weight wood x2',fixture.call_method('GetCurrentWeight')==(1.0,True),str(fixture.call_method('GetCurrentWeight'))+' '+fixture.call_method('GetSnapshot').export_text())
 before=fixture.call_method('GetSnapshot').export_text();fixture.call_method('InitializeInventory',(gi,9,99.0));fixture.call_method('InitializeInventory',(gi,9,99.0));check('repeat init preserves items and identity',fixture.call_method('GetSnapshot').export_text()==before)
 write(stack,'ItemId','item.unknown');write(copy_slots[0],'ItemStack',stack);bad=seeded(copy_slots);check('unknown stored item invalid weight',bad.call_method('GetCurrentWeight')==(0.0,False))
 for quantity in (0,-1):
  write(stack,'ItemId','item.wood');write(stack,'Quantity',quantity);write(copy_slots[0],'ItemStack',stack);bad=seeded(copy_slots);check('invalid stored quantity '+str(quantity),bad.call_method('GetCurrentWeight')==(0.0,False))
 for count,weight in ((0,10.0),(4,-1.0)):
  bad=unreal.new_object(bp.generated_class());bad.call_method('InitializeInventory',(gi,count,weight));check('bad capacity rejected '+str((count,weight)),not bad.get_editor_property('Initialized'))
 bad=unreal.new_object(bp.generated_class());bad.call_method('InitializeInventory',(None,4,10.0));check('missing catalog owner rejected',not bad.get_editor_property('Initialized'))
 unready=unreal.new_object(gi_bp.generated_class());bad=unreal.new_object(bp.generated_class());before=bad.call_method('GetSnapshot').export_text();bad.call_method('InitializeInventory',(unready,4,10.0));check('unready catalog leaves state unchanged',not bad.call_method('IsInitialized') and bad.call_method('GetSnapshot').export_text()==before)
 bad.call_method('InitializeInventory',(gi,4,0.0));check('retry with zero weight capacity',bad.call_method('IsInitialized') and bad.call_method('GetCurrentWeight')==(0.0,True))
 r['passed']=True
except Exception:r['error']=traceback.format_exc();r['passed']=False
finally:
 if seed_name:
  B.remove_function_graph(bp,seed_name);B.compile_blueprint(bp)
  r['fixture_removed']=B.find_graph(bp,seed_name) is None
out.write_text(json.dumps(r,indent=2,ensure_ascii=False),encoding='utf-8')
