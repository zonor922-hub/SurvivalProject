"""Independent A11 model: pure Python transitions plus real UE differential replay."""
from dataclasses import dataclass,field
from collections import Counter
import copy,random,math,json,pathlib,traceback,hashlib
MAX=2147483647
DEFS={'item.wood':(20,.5,False),'item.berry':(10,.1,False),'item.a11.model.durable':(1,1.,True),'item.a11.model.big':(MAX,0.,False)}
_seq=0
def fresh_id():
 global _seq
 _seq+=1;return 'new:'+str(_seq)
def key(s):return (s['id'],s['active'],s['dur'] if s['active'] else None)
@dataclass
class Inventory:
 capacity:int=4
 limit:float=100.
 ready:bool=True
 guard:bool=False
 revision:int=0
 slots:list=field(default_factory=list)
 def __post_init__(self):
  if not self.slots:self.slots=[None]*self.capacity
 def weight(self):return sum(DEFS[s['id']][1]*s['q'] for s in self.slots if s)
 def totals(self):
  c=Counter()
  for s in self.slots:
   if s:c[key(s)]+=s['q']
  return c

def receive(inv,request,transfer=False):
 if request['id'] not in DEFS:return 2,None
 maxq,w,active=DEFS[request['id']]
 if request['active']!=active or (active and (not math.isfinite(request['dur']) or not 0<=request['dur']<=100)):return 5,None
 if inv.weight()+request['q']*w>inv.limit+1.e-5:return 8,None
 result=copy.deepcopy(inv.slots);remaining=request['q']
 for s in result:
  if s and key(s)==key(request) and remaining:
   delta=min(remaining,maxq-s['q'])
   if delta:
    s['q']+=delta;remaining-=delta
    if not transfer:s['dur']=request['dur']
 for i,s in enumerate(result):
  if s is None and remaining:
   delta=min(remaining,maxq);result[i]=dict(request,q=delta,guid=fresh_id());remaining-=delta
 return (9,None) if remaining else (1,result)
def apply(source,dest,kind,request=None,guid=None,q=0,sr=None,dr=None):
 if not source.ready or (kind=='transfer' and (dest is None or not dest.ready)):return 0
 if kind=='transfer' and source is dest:return 16
 if source.guard or (kind=='transfer' and dest.guard):return 7
 if source.revision==MAX or (kind=='transfer' and dest.revision==MAX):return 0
 if kind=='transfer' and (sr!=source.revision or dr!=dest.revision):return 15
 if q<=0:return 6
 if kind=='add':
  code,candidate=receive(source,request)
  if code==1:source.slots=candidate;source.revision+=1
  return code
 if kind=='remove':
  if request['id'] not in DEFS:return 2
  candidate=copy.deepcopy(source.slots);remaining=q
  for i,s in enumerate(candidate):
   if s and s['id']==request['id'] and remaining:
    delta=min(remaining,s['q']);s['q']-=delta;remaining-=delta
    if s['q']==0:candidate[i]=None
  if remaining:return 10
  if sum(DEFS[x['id']][1]*x['q'] for x in candidate if x)>source.limit+1.e-5:return 8
  source.slots=candidate;source.revision+=1;return 1
 if dest.weight()>dest.limit+1.e-5:return 8
 ids=[s['guid'] for o in (source,dest) for s in o.slots if s]
 if len(ids)!=len(set(ids)):return 0
 index=next((i for i,s in enumerate(source.slots) if s and s['guid']==guid),None)
 if index is None:return 11
 original=source.slots[index]
 if q>original['q']:return 10
 taken=dict(original,q=q);code,candidate=receive(dest,taken,True)
 if code!=1:return code
 changes=[i for i,(a,b) in enumerate(zip(dest.slots,candidate)) if a!=b]
 if q==original['q'] and len(changes)==1 and dest.slots[changes[0]] is None:candidate[changes[0]]['guid']=original['guid']
 sc=copy.deepcopy(source.slots)
 if q==original['q']:sc[index]=None
 else:sc[index]['q']-=q
 finalids=[x['guid'] for a in [sc,candidate] for x in a if x]
 if len(finalids)!=len(set(finalids)):return 0
 source.slots=sc;dest.slots=candidate;source.revision+=1;dest.revision+=1;return 1

def pure_checks():
 a,b=Inventory(),Inventory();r={'id':'item.wood','q':10,'active':False,'dur':37.}
 assert apply(a,None,'add',r,q=10)==1
 assert apply(a,b,'transfer',guid=a.slots[0]['guid'],q=3,sr=1,dr=0)==1 and a.totals()+b.totals()==Counter({('item.wood',False,None):10})
 before=copy.deepcopy((a,b));assert apply(a,b,'transfer',guid=a.slots[0]['guid'],q=1,sr=-1,dr=1)==15 and (a,b)==before
 # Model-only forced NewGuid collision must reject both candidates atomically.
 original_factory=globals()['fresh_id'];before=copy.deepcopy((a,b));globals()['fresh_id']=lambda:a.slots[0]['guid']
 try:
  empty=Inventory();old=copy.deepcopy((a,empty));assert apply(a,empty,'transfer',guid=a.slots[0]['guid'],q=1,sr=a.revision,dr=0)==0 and (a,empty)==old
 finally:globals()['fresh_id']=original_factory
 rng=random.Random(20261027);pair=[Inventory(),Inventory()]
 for step in range(1000):
  si=rng.randrange(2);s,d=pair[si],pair[1-si];kind=rng.choice(['transfer','add','remove']);id=rng.choice(list(DEFS));q=rng.choice([-1,0,1,2,9,20,MAX]);request={'id':id,'q':q,'active':DEFS[id][2],'dur':rng.choice([0.,37.,80.,100.])};guid=next((v['guid'] for v in s.slots if v),'unknown');before=copy.deepcopy(pair);old=s.totals()+d.totals();code=apply(s,d,kind,request,guid,q,s.revision,d.revision)
  if code!=1:assert pair==before
  elif kind=='transfer':assert s.totals()+d.totals()==old
  ids=[v['guid'] for inv in pair for v in inv.slots if v];assert len(ids)==len(set(ids));assert all(0<v['q']<=DEFS[v['id']][0] for inv in pair for v in inv.slots if v)
 return True

def run_ue(tests,metrics):
 import unreal
 from inventory_graph_helpers import B,G,P,graph,basic,type_asset,member
 from a09_verify import read,write,snapshot,items,result
 from inventory_event_fixture import listener_class
 bp=unreal.load_asset('/Game/Survival/Inventory/BPC_Inventory');gbp=unreal.load_asset('/Game/Survival/Core/BP_SurvivalGameInstance');dbp=unreal.load_asset('/Game/Survival/Items/Definitions/PDA_ItemDefinition');cbp=unreal.load_asset('/Game/Survival/Items/Catalog/PDA_GameCatalog')
 definitions=[unreal.load_asset('/Game/Survival/Items/Definitions/DA_Item_Wood'),unreal.load_asset('/Game/Survival/Items/Definitions/DA_Item_Berry')]
 for id in ['item.a11.model.durable','item.a11.model.big']:
  d=unreal.new_object(dbp.generated_class());limit,w,active=DEFS[id]
  for k,v in [('ItemId',id),('MaxStack',limit),('UnitWeight',w),('HasDurability',active),('DurabilityMax',100.)]:d.set_editor_property(k,v)
  definitions.append(d)
 cat=unreal.new_object(cbp.generated_class());cat.set_editor_property('Items',definitions);gi=unreal.new_object(gbp.generated_class());gi.set_editor_property('GameCatalog',cat);gi.call_method('InitializeCatalog');assert gi.get_editor_property('CatalogReady')
 for name,prop,t in [('A11ModelGuard','MutationInProgress',basic('bool')),('A11ModelWeight','MaxWeight',basic('real'))]:
  ed=graph(bp,name);v=ed.add_graph_input_parameter('Value',t);member(ed,prop,v,ed.find_graph_entry_pin())
 assert B.compile_blueprint(bp);lbp=listener_class(bp);counts=Counter();failcodes=Counter();overweight=0;bigstates=0;operations=0;history=set();mapping={};guid_objects={};external=Counter()
 class Pair:
  def __init__(self,capacities=(4,4),limits=(100.,100.),unready=False):
   self.models=[Inventory(n,w,ready=not(unready and i==1)) for i,(n,w) in enumerate(zip(capacities,limits))];self.objects=[];self.listeners=[];self.external=Counter()
   for m in self.models:
    o=unreal.new_object(bp.generated_class())
    if m.ready:o.call_method('InitializeInventory',(gi,m.capacity,m.limit))
    self.objects.append(o);x=unreal.new_object(lbp.generated_class());x.call_method('BindInventory',(o,));self.listeners.append(x)
  def guard(self,i,value):self.models[i].guard=value;self.objects[i].call_method('A11ModelGuard',(value,))
  def weight(self,i,value):self.models[i].limit=value;self.objects[i].call_method('A11ModelWeight',(value,))
  def run(self,kind,si=0,di=1,id='item.wood',q=1,dur=0.,guid=None,stale=False):
   nonlocal operations,overweight,bigstates
   s,d=self.models[si],self.models[di];request={'id':id,'q':q,'active':DEFS.get(id,(0,0,False))[2],'dur':dur};sr=s.revision-(1 if stale else 0);dr=d.revision
   if guid is None:guid=next((x['guid'] for x in s.slots if x),'unknown')
   actual_guid=mapping.get(guid,guid)
   old=copy.deepcopy(self.models);before=[snapshot(o).export_text() for o in self.objects];events=[x.get_editor_property('EventCount') for x in self.listeners];oldtot=old[0].totals()+old[1].totals();wasover=s.weight()>s.limit+1.e-5
   code=apply(s,d,kind,request,guid,q,sr,dr)
   if kind=='transfer':
    actual=guid_objects[guid] if guid in guid_objects else (unreal.Guid() if guid=='zero' else unreal.GuidLibrary.new_guid())
    raw=self.objects[si].call_method('TryTransferExact',(self.objects[di],actual,q,sr,dr));response=result(raw[0]);assert raw[1]==d.revision,(operations,kind,'dst revision',raw[1],d.revision)
   else:
    template=read(read(snapshot(self.objects[0]),'Slots')[0],'ItemStack');write(template,'ItemId',id);write(template,'Quantity',q);write(template,'Durability',dur);write(template,'HasDurability',request['active'])
    raw=self.objects[si].call_method('TryAddExact',(template,)) if kind=='add' else self.objects[si].call_method('TryRemoveExact',(id,q));response=result(raw)
   assert response==(code==1,code,q if code==1 else 0,s.revision),(operations,kind,response,code,q,s.revision)
   operations+=1;counts[kind+('_success' if code==1 else '_failure')]+=1
   if kind=='transfer' and code!=1:failcodes[code]+=1
   if kind=='transfer' and code==1 and wasover:overweight+=1
   newtot=self.models[0].totals()+self.models[1].totals()
   if code!=1:assert before==[snapshot(o).export_text() for o in self.objects] and old==self.models
   elif kind=='transfer':
    assert newtot==oldtot
    moved=next(x for x in old[si].slots if x and x['guid']==guid);k=key(moved)
    assert self.models[si].totals()==+(old[si].totals()-Counter({k:q})) and self.models[di].totals()==old[di].totals()+Counter({k:q})
    assert d.weight()<=d.limit+1.e-5 and (s.weight()<=s.limit+1.e-5 or s.weight()<=old[si].weight()+1.e-5)
   elif kind=='add':external[key(request)]+=q;self.external[key(request)]+=q;assert newtot==oldtot+Counter({key(request):q})
   else:
    removed=oldtot-newtot;assert sum(removed.values())==q;self.external.subtract(removed);external.subtract(removed)
   assert newtot==+self.external,('External balance mismatch',operations,newtot,self.external)
   ids=[]
   for i,(m,o) in enumerate(zip(self.models,self.objects)):
    actualslots=list(read(snapshot(o),'Slots'));assert len(actualslots)==(m.capacity if m.ready else 0);assert read(snapshot(o),'Revision')==m.revision
    expected_events=(1 if code==1 and (i==si or kind=='transfer' and i==di) else 0)
    assert self.listeners[i].get_editor_property('EventCount')==events[i]+expected_events
    assert o.get_editor_property('MutationInProgress')==m.guard
    for expected,slot in zip(m.slots,actualslots):
     assert read(slot,'HasItem')==bool(expected)
     if not expected:continue
     st=read(slot,'ItemStack');actualid=read(st,'StackId').export_text();assert unreal.GuidLibrary.is_valid_guid(read(st,'StackId'));ids.append(actualid)
     assert (str(read(st,'ItemId')),read(st,'Quantity'),read(st,'HasDurability'),read(st,'Durability'))==(expected['id'],expected['q'],expected['active'],expected['dur']),(operations,i,expected,st.export_text())
     if expected['guid'] not in mapping:
      assert expected['guid'].startswith('new:') and actualid not in history;mapping[expected['guid']]=actualid;guid_objects[expected['guid']]=read(st,'StackId');history.add(actualid)
     assert mapping[expected['guid']]==actualid
    if m.ready:assert abs(o.call_method('GetCurrentWeight')[0]-m.weight())<=1.e-5
   assert len(ids)==len(set(ids));bigstates+=int(any(v>MAX for v in newtot.values()));return code
 try:
  assert pure_checks();tests.append({'test':'31-M independent model laws','passed':True})
  # A09 Remove still requires its candidate to fit the weight limit.
  p=Pair();p.run('add',q=20);p.weight(0,1.);assert p.run('remove',q=2)==8;assert p.run('remove',q=18)==1
  # Directed coverage is separate from the exact 1800-operation random experiment.
  for cycle in range(60):
   p=Pair();p.run('add',q=20)
   if cycle<20:p.weight(0,1.)
   for j in range(5):
    p.run('transfer',si=j%2,di=1-j%2,q=1)
    if j==0 and cycle<20:p.weight(0,100.)
   p.run('remove',q=1);p.run('remove',si=1,q=1);p.run('add',q=1);p.run('add',q=1)
  for code in [0,16,7,15,6,11,10,9,8]:
   for _ in range(5):
    p=Pair((4,1),unready=code==0);p.run('add',q=20)
    if code==9:p.run('add',si=1,q=20)
    if code==8:p.weight(1,0.)
    if code==7:p.guard(1,True)
    actual=p.run('transfer',di=0 if code==16 else 1,q=0 if code==6 else (21 if code==10 else 1),guid='unknown' if code==11 else None,stale=code==15);assert actual==code
  p=Pair();p.run('add',id='item.a11.model.big',q=MAX);p.run('add',si=1,id='item.a11.model.big',q=MAX)
  for i in range(10):p.run('transfer',si=i%2,di=1-i%2,q=1)
  metrics['random_pairs']=[]
  for index,(caps,limits) in enumerate([((4,4),(10.,10.)),((4,1),(20.,5.)),((8,2),(40.,8.))]):
   rng=random.Random(20261027+index);p=Pair(caps,limits);schedule=['transfer']*300+['add']*180+['remove']*120;rng.shuffle(schedule)
   if index==2:
    p.run('add',q=20);p.weight(0,1.);assert p.models[0].weight()>p.models[0].limit
   for kind in schedule:
    si=rng.randrange(2);di=1-si;id=rng.choice(list(DEFS));q=rng.choice([-1,0,1,1,1,1,2,2,9,20,21,MAX]);dur=rng.choice([0.,37.,80.,100.]);unknown=rng.random()<.2;self_=rng.random()<.05;stale=rng.random()<.1;busy=rng.random()<.05
    if busy:p.guard(si,True)
    p.run(kind,si,si if self_ and kind=='transfer' else di,id,q,dur,guid=('zero' if rng.random()<.5 else 'unknown') if unknown else None,stale=stale)
    if busy:p.guard(si,False)
   metrics['random_pairs'].append({'seed':20261027+index,'capacities':caps,'limits':limits,'operations':600,'transfer':300,'add':180,'remove':120,'initially_overweight_source':index==2})
  assert counts['transfer_success']>=300 and counts['add_success']>=100 and counts['remove_success']>=50
  assert all(failcodes[x]>=5 for x in [0,16,7,15,6,11,10,9,8]) and overweight>=20 and bigstates>=10
  metrics.update(operations=operations,counts=dict(counts),transfer_errors=dict(failcodes),overweight_successes=overweight,large_quantity_states=bigstates,external_balance=dict((str(k),v) for k,v in external.items()))
  tests.append({'test':'31-U real UE differential replay and coverage thresholds','passed':True})
 finally:
  for name in ['A11ModelGuard','A11ModelWeight']:B.remove_function_graph(bp,name)
  assert B.compile_blueprint(bp)
if __name__=='__main__':
 r={'tests':[],'metrics':{},'passed':False}
 try:run_ue(r['tests'],r['metrics']);r['passed']=True
 except Exception:r['error']=traceback.format_exc()
 pathlib.Path(__file__).with_name('a11_model_verification.json').write_text(json.dumps(r,indent=2),encoding='utf-8');assert r['passed'],r.get('error')
