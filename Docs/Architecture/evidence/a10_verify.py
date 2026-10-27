"""A10 contracts against compiled Blueprint; trusted fixtures exist only in memory."""
import unreal,pathlib,json,sys,traceback,time,random,hashlib
from a09_verify import read,write,snapshot,items,result
from inventory_graph_helpers import *
from a10_event_fixture import listener_class

def guard_paths(bp,name):
    """Conservative exhaustive exec traversal of the actual saved command graph."""
    ed=G.get_graph_editor_by_name(bp,name);nodes=list(ed.list_all_nodes())
    entry=next(n for n in nodes if n.get_class().get_name()=='K2Node_FunctionEntry')
    visited=set();returns={};errors=[]
    def walk(node,held=False,acquired=False,released=False,committed=False,path=()):
        key=(node.get_name(),held,acquired,released,committed)
        if key in visited:return
        visited.add(key);path=path+(node.get_name(),)
        cls=node.get_class().get_name()
        if cls=='K2Node_VariableSet':
            guards=[p for p in B.list_all_pins(node) if str(P.get_pin_name(p))=='MutationInProgress']
            if guards:
                assert not P.list_connected_pins(guards[0]),'Dynamic guard assignment needs explicit review'
                held=str(P.get_pin_value(guards[0])).lower()=='true'
                acquired=acquired or held;released=released or not held
        if cls=='K2Node_CallFunction' and str(B.get_node_title(node))=='CommitInventory':
            committed=True;held=False
        if cls=='K2Node_FunctionResult':
            data=list(P.list_connected_pins(pin(node,'Result','INPUT')))
            assert len(data)==1,(name,node.get_name(),'unclassified return')
            producer=P.get_owning_node(data[0]);kind=producer.get_class().get_name()
            if kind=='K2Node_MakeStruct':
                success=pin(producer,'Success','INPUT')
                assert not P.list_connected_pins(success),'Dynamic success needs explicit review'
                assert str(P.get_pin_value(success)).lower()=='false','Unexpected literal success return'
                ok=not acquired or (not held and released)
                label='failure_after_guard' if acquired else 'failure_before_guard'
            else:
                ok=committed and str(B.get_node_title(producer))=='CommitInventory'
                label='commit_result'
            returns[node.get_name()]={'kind':label,'released':released,'ok':ok,'path':list(path)}
            if not ok:errors.append(node.get_name())
            return
        exits=[p for p in B.list_all_pins(node) if 'OUTPUT' in str(P.get_pin_direction(p)) and str(P.get_pin_name(p)) in ('then','else')]
        assert exits,(name,node.get_name(),'Unsupported execution node')
        for p in exits:
            links=list(P.list_connected_pins(p));assert links,(name,node.get_name(),'Unterminated execution path')
            for linked in links:
                assert str(P.get_pin_name(linked))=='execute',(name,node.get_name(),'Non-exec edge')
                walk(P.get_owning_node(linked),held,acquired,released,committed,path)
    walk(entry)
    unreachable=[]
    for n in nodes:
        if n.get_class().get_name()=='K2Node_FunctionResult' and n.get_name() not in returns:
            assert not P.list_connected_pins(pin(n,'execute','INPUT')),'Missed reachable return'
            assert not P.list_connected_pins(pin(n,'Result','INPUT')),'Unreviewed data-connected return'
            unreachable.append(n.get_name())
    after=[r for r in returns.values() if r['kind']=='failure_after_guard']
    assert after and any(r['kind']=='commit_result' for r in returns.values()),'Vacuous graph test'
    return {'passed':not errors,'checked_failure_returns_after_guard':len(after),'returns':returns,'unreachable_empty_default_returns':unreachable,'errors':errors}

def run_suite(gi,bp,tests,metrics):
    def check(name,condition,detail='',category='positive'):
        tests.append({'test':name,'passed':bool(condition),'category':category,'detail':str(detail)});assert condition,(name,detail)
    # Fixture bypasses are temporary, private storage remains closed to gameplay callers.
    for name,field,typ in [('A10SeedSlots','Slots',B.get_array_type(type_asset('FInventorySlot'))),('A10SeedGuard','MutationInProgress',basic('bool')),('A10SeedRevision','Revision',basic('int')),('A10SeedWeightLimit','MaxWeight',basic('real'))]:
        assert not B.find_graph(bp,name);ed=graph(bp,name);v=ed.add_graph_input_parameter('Value',typ);member(ed,field,v,ed.find_graph_entry_pin())
    assert B.compile_blueprint(bp)
    receiver_bp=listener_class(bp)
    def new(count=4,weight=100.,catalog=gi):
        o=unreal.new_object(bp.generated_class());o.call_method('InitializeInventory',(catalog,count,weight));return o
    def add(o,q,id='item.wood'):
        s=read(read(snapshot(new()),'Slots')[0],'ItemStack');write(s,'ItemId',id);write(s,'Quantity',q);r=result(o.call_method('TryAddExact',(s,)));assert r[0],r
    def receiver(o):
        x=unreal.new_object(receiver_bp.generated_class());x.call_method('BindInventory',(o,));return x
    def slots(o):return list(read(snapshot(o),'Slots'))
    def stack(o,index):return read(slots(o)[index],'ItemStack')
    def ident(o,index):return read(stack(o,index),'StackId')
    def split(o,q=4,target=1,id=None):return o.call_method('TrySplit',(id if id is not None else ident(o,0),q,target))
    def merge(o,source=1,target=0):return o.call_method('TryMerge',(ident(o,source),ident(o,target)))
    def total(o):return sum(read(s,'Quantity') for s in items(o))
    def fail(name,o,action,code,listener=None,busy=False):
        x=listener if listener is not None else receiver(o);before=snapshot(o).export_text();events=x.get_editor_property('EventCount');r=result(action())
        check(name+' result',r[:3]==(False,code,0),r,'negative')
        check(name+' snapshot/quantity/GUID/slots/revision unchanged',snapshot(o).export_text()==before,category='negative')
        check(name+' result revision unchanged',r[3]==read(snapshot(o),'Revision'),r,'negative')
        check(name+' no event',x.get_editor_property('EventCount')==events,category='negative')
        check(name+' guard ownership',o.get_editor_property('MutationInProgress')==busy,category='negative')
    o=new();add(o,10);x=receiver(o);original=ident(o,0).export_text();weight=o.call_method('GetCurrentWeight');rev=read(snapshot(o),'Revision')
    r=result(split(o));check('10 wood split 6+4',r==(True,1,4,rev+1) and [read(s,'Quantity') for s in items(o)]==[6,4],r)
    check('split conserves weight and count',o.call_method('GetCurrentWeight')==weight and total(o)==10)
    new_id=ident(o,1);check('split keeps source GUID',ident(o,0).export_text()==original)
    check('split mints unique nonzero GUID',unreal.GuidLibrary.is_valid_guid(new_id) and new_id.export_text()!=original)
    check('split event exactly once after commit',x.get_editor_property('EventCount')==1 and x.get_editor_property('LastRevision')==rev+1 and x.get_editor_property('ObservedRevision')==rev+1)
    check('split changed slots exact order',[int(i) for i in x.get_editor_property('LastChanged')]==[0,1])
    r=result(merge(o));check('merge 6+4 back to 10',r==(True,1,4,rev+2) and total(o)==10 and len(items(o))==1,r)
    check('merge target GUID retained, source absent',ident(o,0).export_text()==original and all(read(s,'StackId').export_text()!=new_id.export_text() for s in items(o)))
    check('merge empty slot canonical',not read(slots(o)[1],'HasItem') and not unreal.GuidLibrary.is_valid_guid(ident(o,1)) and read(stack(o,1),'Quantity')==0)
    check('merge conserves weight',o.call_method('GetCurrentWeight')==weight)
    check('merge one event and committed revision',x.get_editor_property('EventCount')==2 and x.get_editor_property('ObservedRevision')==rev+2)
    check('merge changed slots source then target',list(x.get_editor_property('LastChanged'))==[1,0])
    check('success releases guard',not o.get_editor_property('MutationInProgress'))
    fail('removed source GUID',o,lambda:o.call_method('TryMerge',(new_id,ident(o,0))),11)
    for q in (0,-1,10,11,2147483647):fail('split quantity '+str(q),o,lambda q=q:split(o,q),6)
    for name,id in [('zero',unreal.Guid()),('unknown',unreal.GuidLibrary.new_guid())]:
        fail('split '+name+' GUID',o,lambda id=id:split(o,id=id),11)
        fail('merge '+name+' source',o,lambda id=id:o.call_method('TryMerge',(id,ident(o,0))),11)
        fail('merge '+name+' target',o,lambda id=id:o.call_method('TryMerge',(ident(o,0),id)),11)
    for index in (-1,4,2147483647):fail('split invalid slot '+str(index),o,lambda index=index:split(o,target=index),12)
    fail('split source slot occupied',o,lambda:split(o,target=0),9)
    add(o,1,'item.stone');fail('split occupied other slot',o,lambda:split(o),9)
    fail('merge different ItemId',o,lambda:merge(o),13)
    fail('merge self',o,lambda:merge(o,0,0),11)
    full=new(count=1);add(full,10);fail('split no free slot',full,lambda:split(full,target=0),9)
    crowded=new();add(crowded,21);fail('merge above MaxStack exact rejection',crowded,lambda:merge(crowded),14)
    # Check both commands in a pre-existing critical section; never clear another owner's guard.
    o.call_method('A10SeedGuard',(True,));fail('busy split',o,lambda:split(o),7,busy=True);fail('busy merge',o,lambda:merge(o),7,busy=True);o.call_method('A10SeedGuard',(False,))
    check('owner releases guard after busy tests',not o.get_editor_property('MutationInProgress'))
    # WeightLimit=8 is the established capacity error (A09 add overflow contract).
    overweight=new();add(overweight,10);overweight.call_method('A10SeedWeightLimit',(4.,))
    fail('overweight state split',overweight,lambda:split(overweight),8)
    overweight_merge=new();add(overweight_merge,10);assert result(split(overweight_merge))[0]
    overweight_merge.call_method('A10SeedWeightLimit',(4.,));fail('overweight state merge',overweight_merge,lambda:merge(overweight_merge),8)
    tolerance=new();add(tolerance,10);tolerance.call_method('A10SeedWeightLimit',(5.-1.e-6,));observer=receiver(tolerance)
    assert abs(read(snapshot(tolerance),'MaxWeight')-(5.-1.e-6))<1.e-12,'Weight fixture must preserve double precision'
    check('overweight within tolerance split',result(split(tolerance))==(True,1,4,2) and total(tolerance)==10 and observer.get_editor_property('EventCount')==1 and not tolerance.get_editor_property('MutationInProgress'))
    beyond=new();add(beyond,10);beyond.call_method('A10SeedWeightLimit',(5.-1.e-3,));fail('overweight beyond tolerance split',beyond,lambda:split(beyond),8)
    for command in ('TrySplit','TryMerge'):
        analysis=guard_paths(bp,command);metrics[command+'_guard_paths']=analysis
        check(command+' failure returns release guard',analysis['passed'],analysis['checked_failure_returns_after_guard'])
    raw=unreal.new_object(bp.generated_class());fail('uninitialized split',raw,lambda:raw.call_method('TrySplit',(unreal.GuidLibrary.new_guid(),1,1)),0)
    fail('uninitialized merge',raw,lambda:raw.call_method('TryMerge',(unreal.GuidLibrary.new_guid(),unreal.GuidLibrary.new_guid())),0)
    # Preserve inactive payload exactly on split (inactive durability is not a merge discriminator).
    payload=new();add(payload,10);seed=slots(payload);s=read(seed[0],'ItemStack');write(s,'Durability',37.25);write(seed[0],'ItemStack',s);payload.call_method('A10SeedSlots',(seed,));assert result(split(payload))[0]
    check('split copies ItemId, durability and flag',all(str(read(s,'ItemId'))=='item.wood' and read(s,'Durability')==37.25 and not read(s,'HasDurability') for s in items(payload)))
    # Valid durable fixtures have MaxStack=1 in the MVP, so successful durable merge is forbidden by capacity.
    dbp=unreal.load_asset('/Game/Survival/Items/Definitions/PDA_ItemDefinition');d=unreal.new_object(dbp.generated_class())
    for k,v in [('ItemId','item.audit.durable'),('MaxStack',1),('UnitWeight',1.),('HasDurability',True),('DurabilityMax',100.)]:d.set_editor_property(k,v)
    cat=unreal.new_object(unreal.load_asset('/Game/Survival/Items/Catalog/PDA_GameCatalog').generated_class());cat.set_editor_property('Items',[d]);dgi=unreal.new_object(gi.get_class());dgi.set_editor_property('GameCatalog',cat);dgi.call_method('InitializeCatalog');assert dgi.get_editor_property('CatalogReady')
    durable=new(catalog=dgi);seed=slots(durable)
    for i,dur in ((0,30.),(1,50.)):
        s=read(seed[i],'ItemStack')
        for k,v in [('ItemId','item.audit.durable'),('Quantity',1),('StackId',unreal.GuidLibrary.new_guid()),('HasDurability',True),('Durability',dur)]:write(s,k,v)
        write(seed[i],'ItemStack',s);write(seed[i],'HasItem',True)
    durable.call_method('A10SeedSlots',(seed,));fail('merge incompatible active durability',durable,lambda:merge(durable),13)
    s=read(seed[1],'ItemStack');write(s,'Durability',30.);write(seed[1],'ItemStack',s);durable.call_method('A10SeedSlots',(seed,));fail('durable MaxStack one',durable,lambda:merge(durable),14)
    fail('durable split cannot divide a single item',durable,lambda:split(durable,1,2),6)
    # Zero-weight large-stack data proves the int32 sum is checked before addition.
    large_def=unreal.new_object(dbp.generated_class())
    for k,v in [('ItemId','item.audit.large'),('MaxStack',2147483647),('UnitWeight',0.),('HasDurability',False)]:large_def.set_editor_property(k,v)
    large_cat=unreal.new_object(cat.get_class());large_cat.set_editor_property('Items',[large_def]);large_gi=unreal.new_object(gi.get_class());large_gi.set_editor_property('GameCatalog',large_cat);large_gi.call_method('InitializeCatalog')
    large=new(catalog=large_gi);seed=slots(large)
    for i,q in ((0,2147483646),(1,2)):
        s=read(seed[i],'ItemStack')
        for k,v in [('ItemId','item.audit.large'),('Quantity',q),('StackId',unreal.GuidLibrary.new_guid())]:write(s,k,v)
        write(seed[i],'ItemStack',s);write(seed[i],'HasItem',True)
    large.call_method('A10SeedSlots',(seed,));fail('int32 merge overflow rejected',large,lambda:merge(large),14)
    s=read(seed[1],'ItemStack');write(s,'Quantity',1);write(seed[1],'ItemStack',s);large.call_method('A10SeedSlots',(seed,));r=result(merge(large))
    check('merge exactly int32 MaxStack',r[0] and total(large)==2147483647 and large.call_method('GetCurrentWeight')==(0.,True))
    for defect in ('duplicate GUID','zero GUID','zero quantity','over MaxStack','wrong slot index','unknown item','wrong HasDurability'):
        bad=new();add(bad,21);seed=slots(bad);s=read(seed[0],'ItemStack')
        if defect=='duplicate GUID':write(s,'StackId',read(read(seed[1],'ItemStack'),'StackId'))
        elif defect=='zero GUID':write(s,'StackId',unreal.Guid())
        elif defect=='zero quantity':write(s,'Quantity',0)
        elif defect=='over MaxStack':write(s,'Quantity',21)
        elif defect=='wrong slot index':write(seed[0],'SlotIndex',99)
        elif defect=='unknown item':write(s,'ItemId','item.unknown')
        else:write(s,'HasDurability',True)
        write(seed[0],'ItemStack',s);bad.call_method('A10SeedSlots',(seed,))
        # Use a valid request ID so malformed current state is the first relevant failure.
        request=ident(bad,1)
        fail('corrupt '+defect+' split',bad,lambda bad=bad,request=request:split(bad,1,2,request),0)
        fail('corrupt '+defect+' merge',bad,lambda bad=bad,request=request:bad.call_method('TryMerge',(request,unreal.GuidLibrary.new_guid())),0)
    for mode in (1,2):
        nested=new();add(nested,10)
        if mode==2:assert result(split(nested))[0]
        a,b=receiver(nested),receiver(nested);a.set_editor_property('ReenterMode',mode);a.set_editor_property('Reenter',True)
        start=read(snapshot(nested),'Revision');r=result(split(nested) if mode==1 else merge(nested))
        check('reentrant '+str(mode)+' outer result revision',r[0] and r[3]==start+1)
        check('reentrant '+str(mode)+' two commits and no loss',read(snapshot(nested),'Revision')==start+2 and total(nested)==10 and nested.call_method('GetCurrentWeight')==(5.,True))
        check('reentrant '+str(mode)+' both subscribers exactly two events',a.get_editor_property('EventCount')==2 and b.get_editor_property('EventCount')==2)
        check('reentrant '+str(mode)+' guard clear',not nested.get_editor_property('MutationInProgress'))
    ceiling=new();add(ceiling,10);ceiling.call_method('A10SeedRevision',(2147483646,));assert result(split(ceiling))[0]
    check('revision reaches int32 ceiling without wrap',read(snapshot(ceiling),'Revision')==2147483647);fail('revision overflow rejected',ceiling,lambda:merge(ceiling),0)
    # Bounded reliability/cost sample, not a GPU benchmark or universal frame budget.
    stable=new();add(stable,20);x=receiver(stable);history=set();started=time.perf_counter();rng=random.Random(1010)
    for i in range(100):
        quantity=rng.randint(1,19);assert result(split(stable,quantity))[0];id=ident(stable,1).export_text();assert id not in history;history.add(id);assert result(merge(stable))[0];assert total(stable)==20
    metrics['roundtrip_pairs']=100;metrics['roundtrip_elapsed_seconds']=time.perf_counter()-started
    check('100 split/merge pairs no GUID reuse or loss',len(history)==100 and total(stable)==20 and stable.call_method('GetCurrentWeight')==(10.,True))
    check('100 pairs emit 200 events and revisions',x.get_editor_property('EventCount')==200 and read(snapshot(stable),'Revision')==201)
    check('inventory tick disabled',not stable.is_component_tick_enabled())
    # Independent quantity/identity model: mixed accepted/rejected commands, fixed seed.
    modeled=new();add(modeled,20);observer=receiver(modeled)
    quantities=[20,0,0,0];ids=[ident(modeled,0).export_text(),None,None,None]
    model_revision=1;model_events=0;rng=random.Random(101027)
    for step in range(200):
        occupied=[i for i,q in enumerate(quantities) if q]
        source=rng.choice(occupied);target=rng.randrange(4)
        before=snapshot(modeled).export_text()
        if rng.randrange(2)==0:
            q=rng.randrange(-1,22)
            accepted=source!=target and quantities[target]==0 and 0<q<quantities[source]
            response=result(split(modeled,q,target,ident(modeled,source)))
            if accepted:
                quantities[source]-=q;quantities[target]=q
                ids[target]=ident(modeled,target).export_text()
        else:
            # Empty targets use a valid but unknown ID; the model expects rejection.
            target_id=ident(modeled,target) if quantities[target] else unreal.GuidLibrary.new_guid()
            accepted=source!=target and quantities[target]>0 and quantities[source]+quantities[target]<=20
            response=result(modeled.call_method('TryMerge',(ident(modeled,source),target_id)))
            if accepted:
                quantities[target]+=quantities[source];quantities[source]=0;ids[source]=None
        assert response[0]==bool(accepted),(step,response,accepted)
        if accepted:model_revision+=1;model_events+=1
        else:assert snapshot(modeled).export_text()==before,step
        for index,quantity in enumerate(quantities):
            assert read(slots(modeled)[index],'HasItem')==bool(quantity),(step,index)
            assert read(stack(modeled,index),'Quantity')==quantity,(step,index)
            if quantity:assert ident(modeled,index).export_text()==ids[index],(step,index)
            else:assert not unreal.GuidLibrary.is_valid_guid(ident(modeled,index)),(step,index)
        assert total(modeled)==20 and modeled.call_method('GetCurrentWeight')==(10.,True),step
        assert read(snapshot(modeled),'Revision')==model_revision,step
        assert observer.get_editor_property('EventCount')==model_events,step
        assert not modeled.get_editor_property('MutationInProgress'),step
    metrics['independent_model_operations']=200
    check('200 mixed commands match independent quantity GUID revision event model',model_events==observer.get_editor_property('EventCount') and model_revision==read(snapshot(modeled),'Revision'))
    # Non-binary fractional weight exercises tolerance rather than only exact halves.
    fractional_def=unreal.new_object(dbp.generated_class())
    for k,v in [('ItemId','item.audit.fractional'),('MaxStack',20),('UnitWeight',0.1),('HasDurability',False)]:fractional_def.set_editor_property(k,v)
    fractional_cat=unreal.new_object(cat.get_class());fractional_cat.set_editor_property('Items',[fractional_def])
    fractional_gi=unreal.new_object(gi.get_class());fractional_gi.set_editor_property('GameCatalog',fractional_cat);fractional_gi.call_method('InitializeCatalog')
    fractional=new(catalog=fractional_gi);add(fractional,7,'item.audit.fractional');initial_weight=fractional.call_method('GetCurrentWeight')[0]
    check('fractional 0.1 weight split conserves seven items',result(split(fractional,3))[0] and total(fractional)==7 and abs(fractional.call_method('GetCurrentWeight')[0]-initial_weight)<1.e-5)
    check('fractional 0.1 weight merge conserves seven items',result(merge(fractional))[0] and total(fractional)==7 and abs(fractional.call_method('GetCurrentWeight')[0]-initial_weight)<1.e-5)
    unequal=[(n,q) for n in range(2,21) for q in range(1,n) if 0.1*n != 0.1*(n-q)+0.1*q]
    metrics['fractional_inequivalent_pairs']=unequal
    assert len(unequal)>=30,('Float sweep does not exercise rounding',len(unequal))
    check('fractional sweep inequivalent float sums present',len(unequal)>=30,len(unequal))
    split_failures=[];merge_failures=[];swept=0
    for n in range(2,21):
        for q in range(1,n):
            exact=new(weight=n*0.1,catalog=fractional_gi)
            add(exact,n,'item.audit.fractional') # A09 failure must not be bypassed.
            receiver_exact=receiver(exact);original=ident(exact,0).export_text();weight=exact.call_method('GetCurrentWeight')[0]
            revision=read(snapshot(exact),'Revision');response=result(split(exact,q))
            good=response==(True,1,q,revision+1) and [read(s,'Quantity') for s in items(exact)]==[n-q,q] and abs(exact.call_method('GetCurrentWeight')[0]-weight)<=1.e-5 and not exact.get_editor_property('MutationInProgress') and receiver_exact.get_editor_property('EventCount')==1
            if not good:split_failures.append((n,q,response))
            if response[0]:
                response=result(merge(exact))
                good=response==(True,1,q,revision+2) and total(exact)==n and len(items(exact))==1 and ident(exact,0).export_text()==original and abs(exact.call_method('GetCurrentWeight')[0]-weight)<=1.e-5 and not exact.get_editor_property('MutationInProgress') and receiver_exact.get_editor_property('EventCount')==2
                if not good:merge_failures.append((n,q,response))
            else:merge_failures.append((n,q,'split rejected; merge not possible'))
            swept+=1
    metrics['fractional_sweep_pairs']=swept
    check('fractional sweep split at exact limit',swept==190 and not split_failures,split_failures)
    check('fractional sweep merge at exact limit',swept==190 and not merge_failures,merge_failures)

if __name__=='__main__':
    asset_file=pathlib.Path(unreal.Paths.project_dir())/'Content/Survival/Inventory/BPC_Inventory.uasset'
    initial_asset_hash=hashlib.sha256(asset_file.read_bytes()).hexdigest()
    r={'tests':[],'metrics':{'sensitivity':{'status':'NOT RUN — нет безопасной изоляции','reason':'UE Python exposes no transient Blueprint/graph duplication in BlueprintEditorLibrary/BlueprintGraphEditor. EditorAssetLibrary.duplicate_loaded_asset targets a Content Browser asset path and checks out a file; safe in-memory isolation is not guaranteed. No source connections were modified. Acceptance of this residual risk requires a separate decision.'}}};bp=None
    try:
        bp=unreal.load_asset('/Game/Survival/Inventory/BPC_Inventory');gi=unreal.new_object(unreal.load_asset('/Game/Survival/Core/BP_SurvivalGameInstance').generated_class());gi.call_method('InitializeCatalog')
        run_suite(gi,bp,r['tests'],r['metrics']);r['passed']=True
    except Exception:r['passed']=False;r['error']=traceback.format_exc()
    finally:
        try:
            if bp:
                for name in ('A10SeedSlots','A10SeedGuard','A10SeedRevision','A10SeedWeightLimit'):B.remove_function_graph(bp,name)
                assert B.compile_blueprint(bp)
        except Exception:r['passed']=False;r['cleanup_error']=traceback.format_exc()
        final_asset_hash=hashlib.sha256(asset_file.read_bytes()).hexdigest()
        r['metrics']['source_blueprint_sha256_before']=initial_asset_hash
        r['metrics']['source_blueprint_sha256_after']=final_asset_hash
        if initial_asset_hash!=final_asset_hash:r['passed']=False;r['source_changed_error']='Source Blueprint file changed during unsaved fixture checks'
    pathlib.Path(__file__).with_name('a10_verification.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8')
    assert r['passed'],r.get('error',r.get('cleanup_error'))
