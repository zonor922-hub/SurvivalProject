"""A09 behavioral tests against compiled Blueprint, no asset mutation/save."""
import unreal,json,pathlib,re,traceback,sys
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from inventory_graph_helpers import *
def field(obj,n):
    m=re.search(r'(?<!\w)('+re.escape(n)+r'_\d+_[A-F0-9]+)=',obj.export_text());assert m,(n,obj.export_text());return m.group(1)
def read(obj,n):return obj.get_editor_property(field(obj,n))
def write(obj,n,v):obj.set_editor_property(field(obj,n),v)
def snapshot(o):return o.call_method('GetSnapshot')
def items(o):return [read(s,'ItemStack') for s in read(snapshot(o),'Slots') if read(s,'HasItem')]
def quantities(o):return [read(s,'Quantity') for s in items(o)]
def result(r):return (read(r,'Success'),read(r,'ErrorCode').value,read(r,'ActualQuantity'),read(r,'NewRevision'))

def suite(gi,bp,tests=None):
    tests=[] if tests is None else tests
    guard_name='A09TestSetGuard'
    ed=graph(bp,guard_name);v=ed.add_graph_input_parameter('Guard',basic('bool'));member(ed,'MutationInProgress',v,ed.find_graph_entry_pin());assert B.compile_blueprint(bp)
    ed=graph(bp,'A09TestSetSlots');v=ed.add_graph_input_parameter('SeedSlots',B.get_array_type(type_asset('FInventorySlot')));member(ed,'Slots',v,ed.find_graph_entry_pin());assert B.compile_blueprint(bp)
    def check(label,condition,detail=''):
        tests.append({'test':label,'passed':bool(condition),'detail':str(detail)});assert condition,(label,detail)
    def new(count=4,weight=100.0):
        o=unreal.new_object(bp.generated_class());o.call_method('InitializeInventory',(gi,count,weight));return o
    def stack(qty,ident='item.wood',durable=False,durability=0.0):
        v=read(read(snapshot(new()),'Slots')[0],'ItemStack');write(v,'ItemId',ident);write(v,'Quantity',qty);write(v,'HasDurability',durable);write(v,'Durability',durability);return v
    def add(o,qty,ident='item.wood',**kwargs):return o.call_method('TryAddExact',(stack(qty,ident,**kwargs),))
    def remove(o,qty,ident='item.wood'):return o.call_method('TryRemoveExact',(ident,qty))
    def unchanged(label,o,action,code):
        before=snapshot(o).export_text();r=result(action());check(label,r[:3]==(False,code,0) and snapshot(o).export_text()==before and r[3]==read(snapshot(o),'Revision'),r)
        check(label+' releases guard',not o.get_editor_property('MutationInProgress'))
    o=new();r=result(add(o,21));check('add 21 wood -> 20+1',r==(True,1,21,1) and quantities(o)==[20,1],(r,quantities(o)))
    check('weight 10.5',o.call_method('GetCurrentWeight')==(10.5,True))
    ids=[read(s,'StackId').export_text() for s in items(o)];check('new stacks unique nonzero GUID',len(ids)==len(set(ids)) and all(unreal.GuidLibrary.is_valid_guid(read(s,'StackId')) for s in items(o)))
    r=result(remove(o,2));check('remove 2 exact',r==(True,1,2,2) and quantities(o)==[18,1],(r,quantities(o)))
    check('remove preserves remaining GUIDs',[read(s,'StackId').export_text() for s in items(o)]==ids)
    r=result(remove(o,19));check('remove across distributed stacks',r==(True,1,19,3) and items(o)==[],r)
    check('empty slots canonical',all(not read(s,'HasItem') and not unreal.GuidLibrary.is_valid_guid(read(read(s,'ItemStack'),'StackId')) for s in read(snapshot(o),'Slots')))
    for q in (0,-1,-2147483648):
        unchanged('reject add qty '+str(q),o,lambda q=q:add(o,q),6)
        unchanged('reject remove qty '+str(q),o,lambda q=q:remove(o,q),6)
    unchanged('reject unknown add',o,lambda:add(o,1,'item.unknown'),2)
    unchanged('reject unknown remove',o,lambda:remove(o,1,'item.unknown'),2)
    unchanged('reject empty ID',o,lambda:add(o,1,'None'),2)
    limited=new(weight=10);unchanged('reject weight overflow',limited,lambda:add(limited,21),8)
    small=new(count=1);unchanged('reject slot overflow after simulation',small,lambda:add(small,21),9)
    add(small,19);unchanged('reject partial merge plus no slot',small,lambda:add(small,2),9)
    unchanged('reject insufficient removal after simulation',small,lambda:remove(small,20),10)
    unchanged('reject absent known item',small,lambda:remove(small,1,'item.stone'),10)
    r=result(add(small,1));check('merge retains target GUID and MaxStack',r[0] and quantities(small)==[20])
    unchanged('reject durability flag mismatch',o,lambda:add(o,1,durable=True,durability=10),5)
    raw=unreal.new_object(bp.generated_class());unchanged('reject uninitialized add',raw,lambda:add(raw,1),0)
    unchanged('reject uninitialized remove',raw,lambda:remove(raw,1),0)
    before=snapshot(o).export_text();o.call_method(guard_name,(True,))
    for label,action in [('add',lambda:add(o,1)),('remove',lambda:remove(o,1))]:
        r=result(action());check('guard blocks '+label,r[:3]==(False,7,0) and snapshot(o).export_text()==before and o.get_editor_property('MutationInProgress'),r)
    o.call_method(guard_name,(False,))
    add(o,5);before=snapshot(o).export_text();o.call_method('InitializeInventory',(gi,9,999.0));check('reinit preserves committed items',snapshot(o).export_text()==before)
    # Add mints IDs; a caller-supplied existing ID cannot duplicate a live stack identity.
    supplied=stack(21);write(supplied,'StackId',read(items(o)[0],'StackId'));r=o.call_method('TryAddExact',(supplied,));check('caller GUID never duplicates inventory IDs',read(r,'Success') and len({read(s,'StackId').export_text() for s in items(o)})==len(items(o)))
    import inventory_event_fixture,importlib;importlib.reload(inventory_event_fixture)
    from inventory_event_fixture import listener_class
    receiver_bp=listener_class(bp);receiver=unreal.new_object(receiver_bp.generated_class());tracked=new();receiver.call_method('BindInventory',(tracked,))
    r=result(add(tracked,21));check('success emits exactly one event',receiver.get_editor_property('EventCount')==1,(r,receiver.get_editor_property('EventCount'),receiver.get_editor_property('Inventory')))
    check('event observes committed revision',receiver.get_editor_property('LastRevision')==1 and receiver.get_editor_property('ObservedRevision')==1)
    check('event reports exact changed indices',list(receiver.get_editor_property('LastChanged'))==[0,1])
    unchanged('event failure leaves state',tracked,lambda:remove(tracked,22),10);check('failure emits no event',receiver.get_editor_property('EventCount')==1)
    remove(tracked,2);check('removal emits one event',receiver.get_editor_property('EventCount')==2 and receiver.get_editor_property('LastRevision')==2)
    # A post-commit listener may issue a NEW command. Original result must retain its revision.
    receiver.set_editor_property('Reenter',True);r=result(add(tracked,1))
    check('listener can issue subsequent command after guard release',receiver.get_editor_property('EventCount')==4 and read(snapshot(tracked),'Revision')==4 and sum(quantities(tracked))==19)
    check('outer result retains own committed revision',r==(True,1,1,3),r)
    check('subsequent command guard cleared',not tracked.get_editor_property('MutationInProgress'))
    # Multicast listeners must each receive both commits, without assuming callback order.
    pair_inventory=new();first=unreal.new_object(receiver_bp.generated_class());second=unreal.new_object(receiver_bp.generated_class())
    for listener in (first,second):listener.call_method('BindInventory',(pair_inventory,))
    add(pair_inventory,2)
    check('two subscribers each receive one success',all(x.get_editor_property('EventCount')==1 for x in (first,second)))
    first.set_editor_property('Reenter',True);outer=result(add(pair_inventory,1))
    check('two subscribers receive nested and outer commits',all(x.get_editor_property('EventCount')==3 for x in (first,second)))
    check('nested multicast preserves quantities and outer revision',outer==(True,1,1,2) and read(snapshot(pair_inventory),'Revision')==3 and quantities(pair_inventory)==[2])
    for malformed in ('zero GUID','duplicate GUID','over MaxStack','wrong index','wrong durability'):
        invalid=new();add(invalid,21);slots=list(read(snapshot(invalid),'Slots'));st=read(slots[0],'ItemStack')
        if malformed=='zero GUID':write(st,'StackId',unreal.Guid())
        elif malformed=='duplicate GUID':write(st,'StackId',read(read(slots[1],'ItemStack'),'StackId'))
        elif malformed=='over MaxStack':write(st,'Quantity',21)
        elif malformed=='wrong index':write(slots[0],'SlotIndex',99)
        else:write(st,'HasDurability',True)
        write(slots[0],'ItemStack',st);invalid.call_method('A09TestSetSlots',(slots,))
        unchanged('reject malformed state '+malformed,invalid,lambda:add(invalid,1),0)
    return tests

if __name__=='__main__':
    r={'tests':[]};bp=None
    try:
        bp=unreal.load_asset('/Game/Survival/Inventory/BPC_Inventory');gi=unreal.new_object(unreal.load_asset('/Game/Survival/Core/BP_SurvivalGameInstance').generated_class());gi.call_method('InitializeCatalog')
        suite(gi,bp,r['tests']);r['passed']=True
    except Exception:r['error']=traceback.format_exc();r['passed']=False
    finally:
        try:
            if bp:
                for name in ('A09TestSetGuard','A09TestSetSlots'):B.remove_function_graph(bp,name)
                assert B.compile_blueprint(bp),'Inventory failed to compile after fixture cleanup'
        except Exception:r['cleanup_error']=traceback.format_exc();r['passed']=False
    pathlib.Path(__file__).with_name('a09_verification.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8')
    assert r['passed'],r.get('error')
