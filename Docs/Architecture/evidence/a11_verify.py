"""A11 runtime contracts; trusted fixture functions are never saved."""
import unreal,pathlib,json,sys,traceback,math,collections,hashlib,struct as binary
from inventory_graph_helpers import *
from a09_verify import read,write,snapshot,items,result
from a11_event_fixture import listener_class
FIXTURES=['A11Seed'+n for n in ['Slots','Guard','Revision','Weight','InventoryId']]+['A11CheckInvariants','A11CheckReceive','A11EmitEvent']
def suite(gi,bp,tests,metrics):
 def check(name,ok,detail=''):
  tests.append({'test':name,'passed':bool(ok),'detail':str(detail)});assert ok,(name,detail)
 for name,field,t in [('Slots','Slots',B.get_array_type(type_asset('FInventorySlot'))),('Guard','MutationInProgress',basic('bool')),('Revision','Revision',basic('int')),('Weight','MaxWeight',basic('real')),('InventoryId','InventoryId',B.get_struct_type(unreal.Guid.static_struct()))]:
  ed=graph(bp,'A11Seed'+name);v=ed.add_graph_input_parameter('Value',t);member(ed,field,v,ed.find_graph_entry_pin())
 for alias,methodname in [('A11CheckInvariants','CheckTransferInvariants'),('A11CheckReceive','CheckReceiveExact')]:
  original=G.get_graph_editor_by_name(bp,methodname);en=next(n for n in original.list_all_nodes() if n.get_class().get_name()=='K2Node_FunctionEntry');rn=next(n for n in original.list_all_nodes() if n.get_class().get_name()=='K2Node_FunctionResult');ed=graph(bp,alias)
  args={str(P.get_pin_name(p)):ed.add_graph_input_parameter(str(P.get_pin_name(p)),P.get_pin_type(p)) for p in B.list_all_pins(en) if str(P.get_pin_name(p))!='then'}
  outs={str(P.get_pin_name(p)):P.get_pin_type(p) for p in B.list_all_pins(rn) if str(P.get_pin_name(p))!='execute'};output(ed,**outs);n=method(ed,bp,methodname,ed.find_graph_entry_pin(),**args);ret(ed,nextpin(n),**{k:value(n,k) for k in outs})
 ed=graph(bp,'A11EmitEvent');v=ed.add_graph_input_parameter('Revision',basic('int'));changes=ed.add_graph_input_parameter('ChangedSlots',B.get_array_type(basic('int')));method(ed,bp,'BroadcastChange',ed.find_graph_entry_pin(),Revision=v,ChangedSlots=changes)
 assert B.compile_blueprint(bp);lbp=listener_class(bp)
 def new(n=4,w=100.,catalog=gi,ready=True):
  o=unreal.new_object(bp.generated_class())
  if ready:o.call_method('InitializeInventory',(catalog,n,w))
  return o
 def slots(o):return list(read(snapshot(o),'Slots'))
 def st(o,i=0):return read(slots(o)[i],'ItemStack')
 def ident(o,i=0):return read(st(o,i),'StackId')
 def rev(o):return read(snapshot(o),'Revision')
 def seed(o,field,v):o.call_method('A11Seed'+field,(v,))
 def request(q,id='item.wood',dur=0.,active=False):
  s=st(new());write(s,'ItemId',id);write(s,'Quantity',q);write(s,'Durability',dur);write(s,'HasDurability',active);return s
 def add(o,q,id='item.wood',dur=0.,active=False):
  r=result(o.call_method('TryAddExact',(request(q,id,dur,active),)));assert r[0],r;return r
 watchers=[]
 def obs(o,other=None,mode=0):
  x=unreal.new_object(lbp.generated_class());x.call_method('BindInventory',(o,));x.set_editor_property('Other',other);x.set_editor_property('Mode',mode);watchers.append((o,other,x));return x
 def totals(*inventories):
  d=collections.Counter()
  for o in inventories:
   for s in items(o):d[(str(read(s,'ItemId')),read(s,'HasDurability'),read(s,'Durability') if read(s,'HasDurability') else None)]+=read(s,'Quantity')
  return d
 def snap_totals(sn):
  values=collections.Counter()
  for slot in read(sn,'Slots'):
   if read(slot,'HasItem'):
    stack=read(slot,'ItemStack');values[(str(read(stack,'ItemId')),read(stack,'HasDurability'),read(stack,'Durability') if read(stack,'HasDurability') else None)]+=read(stack,'Quantity')
  return values
 def audit_metadata(label,before,after,selected):
  bits=lambda v:binary.pack('<d',float(v))
  old={read(read(slot,'ItemStack'),'StackId').export_text():read(slot,'ItemStack') for sn in before for slot in read(sn,'Slots') if read(slot,'HasItem')}
  for sn in after:
   for slot in read(sn,'Slots'):
    if not read(slot,'HasItem'):continue
    stack=read(slot,'ItemStack');guid=read(stack,'StackId').export_text();reference=old.get(guid,selected)
    check(label+' bitwise stack metadata '+guid,reference is not None and str(read(stack,'ItemId'))==str(read(reference,'ItemId')) and read(stack,'HasDurability')==read(reference,'HasDurability') and bits(read(stack,'Durability'))==bits(read(reference,'Durability')))
  for pre,post in zip(before,after):
   check(label+' inventory metadata',read(pre,'InventoryId').export_text()==read(post,'InventoryId').export_text() and read(pre,'MaxWeight')==read(post,'MaxWeight'))
   for a,b in zip(read(pre,'Slots'),read(post,'Slots')):
    if a.export_text()==b.export_text():continue
    if read(a,'HasItem') and read(b,'HasItem'):
     av,bv=read(a,'ItemStack'),read(b,'ItemStack')
     if read(av,'StackId').export_text()==read(bv,'StackId').export_text() and read(av,'Quantity')==read(bv,'Quantity'):check(label+' untouched full slot',a.export_text()==b.export_text())
 def transfer(s,d,q,id=None,sr=None,dr=None):
  valid=d is not None and unreal.SystemLibrary.is_valid(d);before=[snapshot(s)]+([snapshot(d)] if valid and d!=s else []);guard=[o.get_editor_property('MutationInProgress') for o in ([s,d] if valid and d!=s else [s])]
  sid=id if id is not None else ident(s);selected=next((read(slot,'ItemStack') for slot in read(before[0],'Slots') if read(slot,'HasItem') and read(read(slot,'ItemStack'),'StackId').export_text()==sid.export_text()),None)
  observer=next((x for own,other,x in watchers if own==s and other==d),None)
  if observer is None:observer=obs(s,d)
  index=len(observer.get_editor_property('AuditOwnSnapshots'));other_index=len(observer.get_editor_property('AuditOtherSnapshots'));tracked=[(own,other,x,x.get_editor_property('EventCount'),x.get_editor_property('Reenter'),x.get_editor_property('Mode')) for own,other,x in watchers if own==s or own==d]
  raw=s.call_method('TryTransferExact',(d,sid,q,rev(s) if sr is None else sr,rev(d) if dr is None and valid else (-1 if dr is None else dr)));ok=result(raw[0])[0]
  metrics['audit40_calls']=metrics.get('audit40_calls',0)+1;label='40 call '+str(metrics['audit40_calls']);metrics['audit40_success' if ok else 'audit40_refusal']=metrics.get('audit40_success' if ok else 'audit40_refusal',0)+1
  if not ok:
   after=[snapshot(s)]+([snapshot(d)] if valid and d!=s else [])
   check(label+' refusal exact snapshots',[sn.export_text() for sn in before]==[sn.export_text() for sn in after]);check(label+' refusal no events',all(x.get_editor_property('EventCount')==count for own,other,x,count,reenter,mode in tracked))
   check(label+' refusal bitwise Durability',all(binary.pack('<d',read(read(a,'ItemStack'),'Durability'))==binary.pack('<d',read(read(b,'ItemStack'),'Durability')) for pre,post in zip(before,after) for a,b in zip(read(pre,'Slots'),read(post,'Slots'))))
   check(label+' refusal guards',guard==[o.get_editor_property('MutationInProgress') for o in ([s,d] if valid and d!=s else [s])]);return raw
  own=list(observer.get_editor_property('AuditOwnSnapshots'));other=list(observer.get_editor_property('AuditOtherSnapshots'));check(label+' committed pair observed',len(own)>index and len(other)>other_index,[index,other_index,len(own),len(other)])
  committed=[own[index],other[other_index]];oldtot=snap_totals(before[0])+snap_totals(before[1]);newtot=snap_totals(committed[0])+snap_totals(committed[1]);key=(str(read(selected,'ItemId')),read(selected,'HasDurability'),read(selected,'Durability') if read(selected,'HasDurability') else None)
  expected_s=snap_totals(before[0]);expected_d=snap_totals(before[1]);expected_s[key]-=q;expected_d[key]+=q
  check(label+' outer conserved2',oldtot==newtot and snap_totals(committed[0])==+expected_s and snap_totals(committed[1])==+expected_d and read(committed[0],'Revision')==read(before[0],'Revision')+1==result(raw[0])[3] and read(committed[1],'Revision')==read(before[1],'Revision')+1==raw[1])
  audit_metadata(label+' outer',before,committed,selected)
  ids=[read(read(slot,'ItemStack'),'StackId').export_text() for sn in committed for slot in read(sn,'Slots') if read(slot,'HasItem')];check(label+' outer unique GUID',len(ids)==len(set(ids)))
  alive=unreal.SystemLibrary.is_valid(d);after=[snapshot(s),snapshot(d) if alive else committed[1]]
  removed=sum((2 if mode==6 else 1) for own,other,x,count,reenter,mode in tracked if reenter and not x.get_editor_property('Reenter') and mode in [1,6])
  expected=oldtot.copy();expected[('item.wood',False,None)]-=removed
  check(label+' callback balance',snap_totals(after[0])+snap_totals(after[1])==+expected)
  audit_metadata(label+' after callbacks',before,after,selected)
  check(label+' restored guards',s.get_editor_property('MutationInProgress')==guard[0] and (not alive or d.get_editor_property('MutationInProgress')==guard[1]))
  if not alive:metrics['audit40_destroyed_observation']=metrics.get('audit40_destroyed_observation',0)+1
  return raw
 def run(label,s,d,q,code=1,id=None,sr=None,dr=None,listeners=None):
  valid=d is not None and unreal.SystemLibrary.is_valid(d);bs=snapshot(s).export_text();bd=snapshot(d).export_text() if valid else None;ts=totals(s,d) if valid else totals(s);rs=rev(s);rd=rev(d) if valid else -1;guards=[s.get_editor_property('MutationInProgress'),d.get_editor_property('MutationInProgress') if valid else False]
  listeners=listeners or [obs(s,d),obs(d,s) if valid else None];counts=[x.get_editor_property('EventCount') if x else 0 for x in listeners]
  sb=slots(s);db=slots(d) if valid else [];source_totals=totals(s);dest_totals=totals(d) if valid else collections.Counter()
  selected=next((read(x,'ItemStack') for x in sb if read(x,'HasItem') and read(read(x,'ItemStack'),'StackId').export_text()==(id if id is not None else ident(s)).export_text()),None)
  source_weight=s.call_method('GetCurrentWeight')[0]
  raw=transfer(s,d,q,id,sr,dr);r,drev=result(raw[0]),raw[1]
  check(label+' result',r==(code==1,code,q if code==1 else 0,rs+(code==1)) and drev==rd+(code==1),[r,drev])
  if code!=1:
   check(label+' unchanged snapshots',snapshot(s).export_text()==bs and (not valid or snapshot(d).export_text()==bd));check(label+' no events',all(not x or x.get_editor_property('EventCount')==c for x,c in zip(listeners,counts)))
  else:
   check(label+' conservation',totals(s,d)==ts)
   key=(str(read(selected,'ItemId')),read(selected,'HasDurability'),read(selected,'Durability') if read(selected,'HasDurability') else None)
   expected_s=source_totals.copy();expected_d=dest_totals.copy();expected_s[key]-=q;expected_d[key]+=q
   check(label+' exact per-side deltas',totals(s)==+expected_s and totals(d)==+expected_d)
   sa,da=slots(s),slots(d);sid=read(selected,'StackId').export_text();bits=lambda v:binary.pack('<d',float(v))
   for before,after in zip(sb,sa):
    if not read(before,'HasItem') or read(read(before,'ItemStack'),'StackId').export_text()!=sid:check(label+' unrelated source slot '+str(read(before,'SlotIndex')),before.export_text()==after.export_text())
   for before,after in zip(db,da):
    if not read(after,'HasItem'):continue
    af=read(after,'ItemStack')
    if read(before,'HasItem'):
     bf=read(before,'ItemStack');check(label+' existing destination metadata '+str(read(before,'SlotIndex')),read(bf,'StackId').export_text()==read(af,'StackId').export_text() and read(bf,'HasDurability')==read(af,'HasDurability') and bits(read(bf,'Durability'))==bits(read(af,'Durability')))
    else:check(label+' new destination metadata '+str(read(after,'SlotIndex')),read(af,'HasDurability')==read(selected,'HasDurability') and bits(read(af,'Durability'))==bits(read(selected,'Durability')))
   dw,dok=d.call_method('GetCurrentWeight');sw,sok=s.call_method('GetCurrentWeight')
   check(label+' weight invariants',dok and sok and dw<=read(snapshot(d),'MaxWeight')+1.e-5 and (sw<=read(snapshot(s),'MaxWeight')+1.e-5 or sw<=source_weight+1.e-5))
   for after in sa:
    if read(after,'HasItem') and read(read(after,'ItemStack'),'StackId').export_text()==sid:
     af=read(after,'ItemStack');check(label+' selected source metadata',all(read(af,n)==read(selected,n) for n in ['ItemId','HasDurability']) and bits(read(af,'Durability'))==bits(read(selected,'Durability')))
   source_changed=[i for i,(b,a) in enumerate(zip(sb,sa)) if b.export_text()!=a.export_text()];dest_changed=[i for i,(b,a) in enumerate(zip(db,da)) if b.export_text()!=a.export_text()]
   check(label+' exact changed slots',list(listeners[0].get_editor_property('LastChanged'))==source_changed and list(listeners[1].get_editor_property('LastChanged'))==dest_changed)
   if q<read(selected,'Quantity'):check(label+' partial source identity',any(read(x,'StackId').export_text()==sid for x in items(s)) and all(read(x,'StackId').export_text()!=sid for x in items(d)))
   elif len(dest_changed)==1 and not read(db[dest_changed[0]],'HasItem'):check(label+' whole identity',read(read(da[dest_changed[0]],'ItemStack'),'StackId').export_text()==sid)
   else:check(label+' merge identity',all(read(x,'StackId').export_text()!=sid for o in [s,d] for x in items(o)))
   ids=[read(x,'StackId').export_text() for o in [s,d] for x in items(o)];check(label+' GUID unique',len(ids)==len(set(ids)))
   check(label+' events after both commits',all(x.get_editor_property('EventCount')==c+1 for x,c in zip(listeners,counts)) and all(x.get_editor_property('OtherObserved').export_text()==snapshot(other).export_text() for x,other in zip(listeners,[d,s])))
   check(label+' changed sorted',all(list(x.get_editor_property('LastChanged'))==sorted(set(x.get_editor_property('LastChanged'))) for x in listeners))
  check(label+' guard ownership',s.get_editor_property('MutationInProgress')==guards[0] and (not valid or d.get_editor_property('MutationInProgress')==guards[1]));return r,drev
 def pair(q=10,dq=0,n=4,w=100.):
  s,d=new(),new(n,w);add(s,q)
  if dq:add(d,dq)
  return s,d
 def compare36(label,before_d,before_control,source_stack,taken,d,control,success):
  ds,cs=slots(d),slots(control);changed=[i for i,(a,b) in enumerate(zip(before_d,ds)) if a.export_text()!=b.export_text()];exceptions=0
  bits=lambda x:binary.pack('<d',float(x))
  for i,(old,oldc,a,b) in enumerate(zip(before_d,before_control,ds,cs)):
   check(label+' slot flags/index '+str(i),read(a,'HasItem')==read(b,'HasItem') and read(a,'SlotIndex')==read(b,'SlotIndex'))
   av,bv,ov=read(a,'ItemStack'),read(b,'ItemStack'),read(old,'ItemStack')
   check(label+' item/count/active '+str(i),all(read(av,n)==read(bv,n) for n in ['ItemId','Quantity','HasDurability']))
   exception=success and read(old,'HasItem') and not read(ov,'HasDurability') and read(av,'Quantity')>read(ov,'Quantity')
   if exception:
    check(label+' exact inactive exception '+str(i),bits(read(av,'Durability'))==bits(read(ov,'Durability')) and bits(read(bv,'Durability'))==bits(read(taken,'Durability')));exceptions+=int(bits(read(av,'Durability'))!=bits(read(bv,'Durability')))
   else:check(label+' strict durability '+str(i),bits(read(av,'Durability'))==bits(read(bv,'Durability')))
   if read(old,'HasItem'):
    check(label+' existing identities '+str(i),read(av,'StackId').export_text()==read(ov,'StackId').export_text() and read(bv,'StackId').export_text()==read(read(oldc,'ItemStack'),'StackId').export_text())
   elif read(a,'HasItem'):
    original=read(source_stack,'StackId').export_text();whole=read(source_stack,'Quantity')==read(taken,'Quantity')
    check(label+' new identity D2 '+str(i),unreal.GuidLibrary.is_valid_guid(read(av,'StackId')) and unreal.GuidLibrary.is_valid_guid(read(bv,'StackId')) and (read(av,'StackId').export_text()==original if whole and len(changed)==1 else read(av,'StackId').export_text()!=original))
   else:check(label+' empty identity '+str(i),read(av,'StackId').export_text()==read(bv,'StackId').export_text())
  metrics['inactive_exception_slots']=metrics.get('inactive_exception_slots',0)+exceptions
  check(label+' weight',abs(d.call_method('GetCurrentWeight')[0]-control.call_method('GetCurrentWeight')[0])<=1.e-5)
 s,d=pair();sid=ident(s).export_text();run('1 partial',s,d,3);check('1 quantities/GUID',[read(x,'Quantity') for x in items(s)]==[7] and read(items(d)[0],'Quantity')==3 and ident(s).export_text()==sid and ident(d).export_text()!=sid)
 s,d=pair();sid=ident(s).export_text();run('2 whole',s,d,10);check('2 GUID retained',not items(s) and ident(d).export_text()==sid)
 for label,q,dq,n in [('3 merge',5,15,20),('4 merge+empty',5,18,20),('4a merge preferred',5,14,19),('4b partial merge',10,15,18)]:
  s,d=pair(q,dq);sid=ident(s).export_text();did=ident(d).export_text();run(label,s,d,3 if label.startswith('4b') else q);check(label+' target GUID',ident(d).export_text()==did and read(st(d),'Quantity')==n)
  if label.startswith('4 merge'):check('4 source GUID disappears',all(read(x,'StackId').export_text()!=sid for o in [s,d] for x in items(o)))
 s,d=pair(20,w=10);run('5 exact weight',s,d,20)
 for id in ['item.berry','item.plank']:
  s,d=new(),new(w=0.7 if id=='item.berry' else 2.8);add(s,7,id);run('6 '+id,s,d,7)
 # Durable, fractional and int32-ceiling definitions are transient catalog data.
 dbp=unreal.load_asset('/Game/Survival/Items/Definitions/PDA_ItemDefinition');cbp=unreal.load_asset('/Game/Survival/Items/Catalog/PDA_GameCatalog')
 definitions=[]
 for id,limit,weight,durable in [('item.a11.fractional',20,0.1,False),('item.a11.durable',1,1.,True),('item.a11.big',2147483647,0.,False),('item.a11.zero',20,0.,False)]:
  definition=unreal.new_object(dbp.generated_class())
  for k,v in [('ItemId',id),('MaxStack',limit),('UnitWeight',weight),('HasDurability',durable),('DurabilityMax',100.)]:definition.set_editor_property(k,v)
  definitions.append(definition)
 catalog=unreal.new_object(cbp.generated_class());catalog.set_editor_property('Items',definitions+[unreal.load_asset('/Game/Survival/Items/Definitions/DA_Item_Wood'),unreal.load_asset('/Game/Survival/Items/Definitions/DA_Item_Berry')]);audit_gi=unreal.new_object(gi.get_class());audit_gi.set_editor_property('GameCatalog',catalog);audit_gi.call_method('InitializeCatalog');assert audit_gi.get_editor_property('CatalogReady')

 metrics['inequivalent_double_pairs']=[(n,q) for n in range(2,21) for q in range(1,n) if 0.1*n!=0.1*(n-q)+0.1*q]
 check('6a double rounding exercised',len(metrics['inequivalent_double_pairs'])>=30)
 # Full 190-pair sweep, empty and merging destination, true runtime transfers.
 for merging in [False,True]:
  swept=0
  for n in range(2,21):
   for q in range(1,n):
    s,d=new(catalog=audit_gi),new(w=(n if merging else q)*0.1,catalog=audit_gi);add(s,n,'item.a11.fractional')
    if merging:add(d,n-q,'item.a11.fractional')
    run('6a '+str((merging,n,q)),s,d,q);swept+=1
  check('6a sweep count '+str(merging),swept==190);metrics['sweep_'+str(merging)]=swept
 s,d=pair(25);first=read(st(s),'Quantity');run('8 exact second stack',s,d,3,id=ident(s,1));check('8 first unchanged',read(st(s),'Quantity')==first and read(st(s,1),'Quantity')==2)
 s,d=pair();run('10 forward',s,d,3);run('10 back',d,s,3);check('10 restored quantities',read(st(s),'Quantity')==10 and not items(d))
 s,d=pair();
 for i in range(3):run('11 sequence '+str(i),s,d,1)
 for label,sq,dq,n,w,q,code in [('12 full',10,20,1,100.,1,9),('13 weight',10,0,4,1.,3,8),('13a epsilon',10,0,4,1.5-1e-6,3,1),('13b epsilon',10,0,4,1.5-1e-3,3,8),('14 partial capacity',10,19,1,100.,2,9)]:
  s,d=pair(sq,dq,n,w);run(label,s,d,q,code)
 s,d=pair();seed(s,'Weight',2.);run('13c overweight source',s,d,2)
 for i in range(2):run('13d unload '+str(i),s,d,2)
 run('13e below limit',s,d,1)
 s,d=pair(w=1.);seed(s,'Weight',2.);run('13f both limits',s,d,3,8)
 s,d=pair(dq=10);seed(d,'Weight',1.);run('13g overweight receiver',s,d,1,8)
 for q in [0,-1,-2147483648]:s,d=pair();run('15 quantity '+str(q),s,d,q,6)
 for q in [11,2147483647]:s,d=pair();run('16 insufficient '+str(q),s,d,q,10)
 s,d=pair();run('17 zero GUID',s,d,1,11,id=unreal.Guid())
 s,d=pair(dq=2);run('18 unknown GUID',s,d,1,11,id=unreal.GuidLibrary.new_guid());run('18 destination GUID',s,d,1,11,id=ident(d))
 for side in ['src','dst']:
  for offset in [-2,-1,1]:
   s,d=pair();run('19 '+str((side,offset)),s,d,1,15,sr=rev(s)+offset if side=='src' else None,dr=rev(d)+offset if side=='dst' else None)
 s,d=pair();run('20 same inventory',s,s,1,16)
 s,d=pair();run('21-1 None',s,None,1,0)
 s,d=pair();d.call_method("K2_DestroyComponent",(d,));run('21-2 destroyed',s,d,1,0,dr=-1)
 s,d=pair();run('21-3 uninitialized receiver',s,new(ready=False),1,0)
 s,d=pair();run('21-4 uninitialized source',new(ready=False),d,1,0,id=unreal.Guid())
 s,d=pair();seed(d,'InventoryId',read(snapshot(s),'InventoryId'));run('21a duplicate InventoryId',s,d,1,0)
 s,d=pair();g2=unreal.new_object(gi.get_class());g2.call_method('InitializeCatalog');d=new(catalog=g2);run('22 catalogs',s,d,1,0)
 for sg,dg in [(True,False),(False,True),(True,True)]:
  s,d=pair();seed(s,'Guard',sg);seed(d,'Guard',dg);run('23 busy '+str((sg,dg)),s,d,1,7);seed(s,'Guard',False);seed(d,'Guard',False);run('23d retry '+str((sg,dg)),s,d,1)
 for which in ['src','dst']:
  for bad in ['zero','duplicate','quantity','index','durability']:
   s,d=pair(25,25);o=s if which=='src' else d;ss=slots(o);v=read(ss[0],'ItemStack')
   if bad=='zero':write(v,'StackId',unreal.Guid())
   elif bad=='duplicate':write(v,'StackId',read(read(ss[1],'ItemStack'),'StackId'))
   elif bad=='quantity':write(v,'Quantity',21)
   elif bad=='index':write(ss[0],'SlotIndex',99)
   else:write(v,'HasDurability',True)
   write(ss[0],'ItemStack',v);seed(o,'Slots',ss);run('24 '+str((which,bad)),s,d,1,0)
 for i,label in [(0,'25 conflict'),(1,'25a unrelated conflict')]:
  s,d=pair(25,1);ss=slots(d);v=read(ss[0],'ItemStack');write(v,'StackId',ident(s,i));write(ss[0],'ItemStack',v);seed(d,'Slots',ss);run(label,s,d,1,0)
 for sv,dv in [(2147483647,0),(1,2147483647),(2147483647,2147483647),(2147483646,2147483646)]:
  s,d=pair();seed(s,'Revision',sv);seed(d,'Revision',dv);run('26 revision '+str((sv,dv)),s,d,1,1 if sv==dv==2147483646 else 0)
  if sv==dv==2147483646:run('26d next rejected',s,d,1,0)
 # Callback reentry, reverse transfer, two subscribers and monotonic mirror.
 for mode in [1,2]:
  s,d=pair();sx,dx=obs(s,d,mode),obs(d,s);sx.set_editor_property('Reenter',True);raw=transfer(s,d,3);rr=result(raw[0]);check('27/28 outer revisions '+str(mode),rr==(True,1,3,2) and raw[1]==1)
  check('27/28 balances '+str(mode),sum(read(x,'Quantity') for x in items(s)+items(d))==10-(mode==1))
  check('27/28 exact per-side and revisions '+str(mode),[read(x,'Quantity') for x in items(s)]==[7 if mode==1 else 8] and [read(x,'Quantity') for x in items(d)]==[2] and rev(s)==(2 if mode==1 else 3) and rev(d)==2)
  check('27/28 guard and event completeness '+str(mode),not s.get_editor_property('MutationInProgress') and not d.get_editor_property('MutationInProgress') and sx.get_editor_property('EventCount')==(1 if mode==1 else 2) and dx.get_editor_property('EventCount')==2)
  check('27/28 metadata and GUID '+str(mode),all(str(read(x,'ItemId'))=='item.wood' and not read(x,'HasDurability') and binary.pack('<d',read(x,'Durability'))==binary.pack('<d',0.) for x in items(s)+items(d)) and len({read(x,'StackId').export_text() for x in items(s)+items(d)})==2)
  check('30a reverse event order '+str(mode),list(dx.get_editor_property('EventHistory'))==[2,1],list(dx.get_editor_property('EventHistory')))
  check('30b-e mirror '+str(mode),dx.get_editor_property('ShownRevision')==rev(d) and dx.get_editor_property('ShownSnapshot').export_text()==snapshot(d).export_text() and dx.get_editor_property('IgnoredStale')>=1 and list(dx.get_editor_property('AppliedHistory'))==sorted(set(dx.get_editor_property('AppliedHistory'))))
 s,d=pair();listeners=[obs(s,d),obs(d,s)];extra=[obs(s,d),obs(d,s)];run('29 two listeners',s,d,3,listeners=listeners);check('29 all receive',all(x.get_editor_property('EventCount')==1 for x in extra))
 # Priority combinations explicitly exercise first error, not isolated failures.
 for name in ['37a','37b','37c','37d','37e','37f','37g','37h','37i','37j','37k','37l','37m']:
  s,d=pair();kwargs={};q=1;code=0
  if name=='37a':s=new(ready=False);seed(d,'Guard',True);kwargs['id']=unreal.Guid()
  elif name=='37b':d=s;kwargs['sr']=-1;code=16
  elif name=='37c':seed(d,'InventoryId',read(snapshot(s),'InventoryId'));seed(s,'Guard',True)
  elif name=='37d':g2=unreal.new_object(gi.get_class());g2.call_method('InitializeCatalog');d=new(catalog=g2);seed(d,'Guard',True)
  elif name=='37e':seed(s,'Guard',True);kwargs['sr']=-1;q=0;code=7
  elif name=='37f':seed(d,'Revision',2147483647);kwargs['dr']=-1
  elif name=='37g':kwargs['sr']=-1;q=0;code=15
  elif name=='37h':kwargs['id']=unreal.Guid();q=0;code=6
  elif name=='37i':ss=slots(d);write(ss[0],'SlotIndex',99);seed(d,'Slots',ss);kwargs['id']=unreal.Guid()
  elif name=='37j':d=new(1);add(d,20);kwargs['id']=unreal.Guid();code=11
  elif name=='37k':d=new(1);add(d,20);q=11;code=10
  elif name=='37l':seed(s,'Weight',1.);add(d,10);seed(d,'Weight',1.);code=8
  else:d=None;seed(s,'Guard',True)
  run(name,s,d,q,code,**kwargs)
 # Durable metadata and inactive durability must survive exact transport.
 for durability in [0.,37.,80.,100.]:
  s,d=new(catalog=audit_gi),new(catalog=audit_gi);add(s,1,'item.a11.durable',durability,True);sid=ident(s).export_text();run('7/7b durable '+str(durability),s,d,1);check('7 metadata '+str(durability),read(st(d),'Durability')==durability and read(st(d),'HasDurability') and ident(d).export_text()==sid)
 s,d=new(catalog=audit_gi),new(catalog=audit_gi)
 for durability in [37.,80.]:
  add(s,1,'item.a11.durable',durability,True);run('7a distinct '+str(durability),s,d,1,id=read(items(s)[0],'StackId'))
 check('7a separate durable stacks',[read(x,'Durability') for x in items(d)]==[37.,80.])
 for merging in [False,True]:
  s,d=pair(10,5 if merging else 0);ss=slots(s);v=read(ss[0],'ItemStack');write(v,'Durability',37.);write(ss[0],'ItemStack',v);seed(s,'Slots',ss)
  if merging:
   ss=slots(d);v=read(ss[0],'ItemStack');write(v,'Durability',80.);write(ss[0],'ItemStack',v);seed(d,'Slots',ss)
  run('7c inactive '+str(merging),s,d,3);check('7c inactive value '+str(merging),read(st(d),'Durability')==(80. if merging else 37.))
 s,d=new(catalog=audit_gi),new(1,catalog=audit_gi);add(s,1,'item.a11.durable',37.,True);add(d,1,'item.a11.durable',80.,True);run('26 durable full',s,d,1,9)
 s,d=pair(25);seed(s,'Weight',1.)
 for methodname,args in [('TryAddExact',(request(1),)),('TrySplit',(ident(s),1,2)),('TryMerge',(ident(s,1),ident(s)))]:
  before=snapshot(s).export_text();rr=result(s.call_method(methodname,args));check('13h '+methodname,rr[:3]==(False,8,0) and snapshot(s).export_text()==before)
 s,d=new(catalog=audit_gi),new(catalog=audit_gi);add(s,1,'item.a11.zero');add(d,10);seed(d,'Weight',1.);run('13g zero-weight incoming',s,d,1,8)
 # Whole GUID collision with a nonparticipant is deliberately outside A11's pair check.
 s,d=pair();third=new();add(third,1);third_before=snapshot(third).export_text();run('25c pair with third present',s,d,3);check('25c third unchanged',snapshot(third).export_text()==third_before and len({read(x,'StackId').export_text() for o in [s,d,third] for x in items(o)})==len(items(s)+items(d)+items(third)))
 # 25c: a bidirectional series, with a rich nonparticipant checked after every command.
 s,d=new(8,catalog=audit_gi),new(8,catalog=audit_gi);add(s,25);add(d,5);third=new(8,catalog=audit_gi);add(third,9);add(third,1,'item.a11.durable',37.,True);add(third,1,'item.a11.durable',80.,True);third_listener=obs(third);third_before=snapshot(third).export_text()
 for i in range(40):
  source,dest=(s,d) if i%2==0 else (d,s);run('25c series '+str(i),source,dest,1+i%3)
  check('25c third exact snapshot '+str(i),snapshot(third).export_text()==third_before and third_listener.get_editor_property('EventCount')==0)
  allids=[read(x,'StackId').export_text() for o in [s,d,third] for x in items(o)];check('25c global GUID series '+str(i),len(allids)==len(set(allids)))
 metrics['third_inventory_series_transfers']=40
 s,d=pair();ss=slots(third);v=read(ss[0],'ItemStack');write(v,'StackId',ident(s));write(ss[0],'ItemStack',v);seed(third,'Slots',ss);run('25c external collision limitation',s,d,10);check('25c expected undetected conflict',ident(d).export_text()==ident(third).export_text())
 # Test the invariant function directly with an otherwise valid synthetic collision.
 s,d=pair();sb,db=slots(s),slots(d);sc,dc=slots(s),slots(d);taken=st(s);write(taken,'Quantity',1);v=read(sc[0],'ItemStack');write(v,'Quantity',9);write(sc[0],'ItemStack',v);write(dc[0],'HasItem',True);write(dc[0],'ItemStack',taken)
 answer=s.call_method('A11CheckInvariants',(sb,db,sc,dc,taken));answer=answer[-1] if isinstance(answer,tuple) else answer;check('25b candidate collision rejected',not answer,repr(answer))
 for many in [False,True]:
  s,d=new(catalog=audit_gi),new(catalog=audit_gi);add(s,2147483647,'item.a11.big');add(d,2147483647 if many else 10,'item.a11.big')
  if many:add(s,2147483647,'item.a11.big')
  count=sum(read(x,'Quantity') for x in items(s)+items(d));run('39a/b int64 '+str(many),s,d,5);check('39 int64 sum '+str(many),sum(read(x,'Quantity') for x in items(s)+items(d))==count and count>2147483647)
 s,d=new(catalog=audit_gi),new(catalog=audit_gi);add(s,2,'item.a11.big');sb,db=slots(s),slots(d);sc,dc=slots(s),slots(d);taken=st(s);write(taken,'Quantity',1);v=read(sc[0],'ItemStack');write(v,'Quantity',1);write(sc[0],'ItemStack',v)
 for i,q in enumerate([2147483647,2147483647,3]):
  v=st(s);write(v,'StackId',unreal.GuidLibrary.new_guid());write(v,'Quantity',q);write(dc[i],'HasItem',True);write(dc[i],'ItemStack',v)
 check('39c int32 alias fixture',sum(read(read(v,'ItemStack'),'Quantity') for v in dc if read(v,'HasItem'))-1==2**32)
 answer=s.call_method('A11CheckInvariants',(sb,db,sc,dc,taken));answer=answer[-1] if isinstance(answer,tuple) else answer;check('39c int64 mismatch rejected',not answer,repr(answer))
 # Differential destination acceptance, order and state against the real A09 command.
 for id,active,durability in [('item.wood',False,0.),('item.a11.fractional',False,0.),('item.a11.durable',True,37.)]:
  for starting,n,limit,q in [(0,4,100.,1),(5,4,100.,3),(20,1,100.,1),(19,1,100.,2),(0,4,0.5,2),(0,4,0.1,1),(20,1,0.5,1)]:
   if active and (starting or q>1):continue
   if id=='item.a11.fractional' and starting>20:continue
   for whole in [True,False] if not active else [True]:
    s,d,control=new(catalog=audit_gi),new(n,100.,audit_gi),new(n,100.,audit_gi)
    if starting:add(d,starting,id,durability,active);add(control,starting,id,durability,active)
    seed(d,'Weight',limit);seed(control,'Weight',limit);add(s,q if whole else q+1,id,durability,active);taken=request(q,id,durability,active);x=obs(control);y=obs(d)
    bd36,bc36,bs36=slots(d),slots(control),st(s)
    expected=result(control.call_method('TryAddExact',(taken,)));actual=result(transfer(s,d,q)[0]);check('36 outcome '+str((id,starting,n,limit,q,whole)),actual[:3]==expected[:3],[actual,expected])
    compare36('36 '+str((id,starting,n,limit,q,whole)),bd36,bc36,bs36,taken,d,control,actual[0])
    check('36 changed slots '+str((id,starting,n,limit,q,whole)),list(x.get_editor_property('LastChanged'))==list(y.get_editor_property('LastChanged')))
 # Explicit approved exception: only existing inactive receiving stacks may differ.
 for starting,n,limit,q,whole in [(5,4,100.,3,False),(18,4,100.,5,True),(0,4,100.,3,False),(5,4,3.,3,False),(19,1,100.,3,False)]:
  s,d,control=new(),new(n),new(n)
  if starting:
   for o in [d,control]:
    add(o,starting);ss=slots(o);v=read(ss[0],'ItemStack');write(v,'Durability',80.);write(ss[0],'ItemStack',v);seed(o,'Slots',ss)
  add(s,q if whole else 10);ss=slots(s);v=read(ss[0],'ItemStack');write(v,'Durability',37.);write(ss[0],'ItemStack',v);seed(s,'Slots',ss)
  for o in [d,control]:seed(o,'Weight',limit)
  taken=request(q,dur=37.);bd36,bc36,bs36=slots(d),slots(control),st(s);sx,dx=obs(s,d),obs(d,s);cx=obs(control)
  expected=result(control.call_method('TryAddExact',(taken,)));actual=run('36 targeted '+str((starting,n,limit,q,whole)),s,d,q,expected[1],listeners=[sx,dx])[0]
  compare36('36 targeted '+str((starting,n,limit,q,whole)),bd36,bc36,bs36,taken,d,control,actual[0]);check('36 targeted changes',list(dx.get_editor_property('LastChanged'))==list(cx.get_editor_property('LastChanged')))
 check('36 approved difference exercised',metrics.get('inactive_exception_slots',0)>=2)
 s,d=pair();oldid=ident(s);run('18 remove original',s,d,10);run('18 disappeared GUID',s,d,1,11,id=oldid)
 # A read-only shared classifier must not alter data, identity, revisions or guard.
 s,d=pair();before=snapshot(s).export_text();x=obs(s)
 for q in [1,200]:s.call_method('A11CheckReceive',(request(q),[],False,False))
 check('shared classifier has no side effects',snapshot(s).export_text()==before and not s.get_editor_property('MutationInProgress') and x.get_editor_property('EventCount')==0)
 # Callback destruction: the write happened first, only the second broadcast is skipped.
 s,d=pair();sx,dx=obs(s,d,4),obs(d,s);sx.set_editor_property('Reenter',True);raw=transfer(s,d,3);check('29a destroyed receiver result',result(raw[0])==(True,1,3,2) and raw[1]==1 and not unreal.SystemLibrary.is_valid(d));check('29a source event only',sx.get_editor_property('EventCount')==1 and dx.get_editor_property('EventCount')==0)

 # Explicit stale callback, dual mirrors and snapshot newer than its triggering event.
 s,d=pair();sx,dx=obs(s,d,3),obs(d,s);sx.set_editor_property('Reenter',True);raw=transfer(s,d,3)
 check('28 stale callback rejected',result(raw[0])==(True,1,3,2) and raw[1]==1 and sx.get_editor_property('NestedError')==15 and not sx.get_editor_property('NestedSuccess') and rev(s)==2 and rev(d)==1)
 check('27/28 callback guards restored',not s.get_editor_property('MutationInProgress') and not d.get_editor_property('MutationInProgress'))
 s,d=pair();sx,dx=obs(s,d,2),obs(d,s,1)
 for x in [sx,dx]:x.set_editor_property('Reenter',True)
 transfer(s,d,3)
 for x,o in [(sx,s),(dx,d)]:
  history=list(x.get_editor_property('AppliedHistory'));check('30d dual mirror '+str(o.get_name()),x.get_editor_property('ShownRevision')==rev(o) and x.get_editor_property('ShownSnapshot').export_text()==snapshot(o).export_text() and history==sorted(set(history)))
 before=[(x.get_editor_property('ShownRevision'),x.get_editor_property('ShownSnapshot').export_text()) for x in [sx,dx]];run('30e stale no mirror update',s,d,1,15,sr=-1,listeners=[sx,dx]);check('30e unchanged mirror values',before==[(x.get_editor_property('ShownRevision'),x.get_editor_property('ShownSnapshot').export_text()) for x in [sx,dx]])
 s,d=pair();sx,late=obs(s,d,6),unreal.new_object(lbp.generated_class());sx.set_editor_property('LateMirror',late);sx.set_editor_property('Reenter',True);transfer(s,d,3)
 check('30c snapshot newer than event applied',list(late.get_editor_property('EventHistory'))==[1] and list(late.get_editor_property('SnapshotHistory'))==[3] and list(late.get_editor_property('AppliedHistory'))==[3] and list(late.get_editor_property('AppliedEventHistory'))==[1] and late.get_editor_property('ShownSnapshot').export_text()==snapshot(d).export_text())
 before=late.get_editor_property('ShownSnapshot').export_text();d.call_method('A11EmitEvent',(2,[]));check('30c intermediate event ignored',late.get_editor_property('ShownRevision')==3 and late.get_editor_property('ShownSnapshot').export_text()==before and late.get_editor_property('IgnoredStale')==1)
 check('40 every wrapped transfer audited',metrics['audit40_calls']==metrics['audit40_success']+metrics['audit40_refusal'] and metrics['audit40_destroyed_observation']==1)
 metrics['contracts_completed']=True
if __name__=='__main__':
 r={'tests':[],'metrics':{},'passed':False};bp=None;asset=pathlib.Path(unreal.Paths.project_dir())/'Content/Survival/Inventory/BPC_Inventory.uasset';before=hashlib.sha256(asset.read_bytes()).hexdigest()
 try:
  bp=unreal.load_asset('/Game/Survival/Inventory/BPC_Inventory');gi=unreal.new_object(unreal.load_asset('/Game/Survival/Core/BP_SurvivalGameInstance').generated_class());gi.call_method('InitializeCatalog');suite(gi,bp,r['tests'],r['metrics']);r['passed']=True
 except Exception:r['error']=traceback.format_exc()
 finally:
  if bp:
   for name in FIXTURES:B.remove_function_graph(bp,name)
   r['cleanup_compile']=B.compile_blueprint(bp)
  r['source_sha256_before']=before;r['source_sha256_after']=hashlib.sha256(asset.read_bytes()).hexdigest();r['passed']=r['passed'] and r.get('cleanup_compile',False) and before==r['source_sha256_after']
 pathlib.Path(__file__).with_name('a11_verification.json').write_text(json.dumps(r,indent=2,ensure_ascii=False),encoding='utf-8');assert r['passed'],r.get('error')
