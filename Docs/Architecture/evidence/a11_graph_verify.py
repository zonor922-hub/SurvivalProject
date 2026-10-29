"""A11 exhaustive saved-graph checks and unsaved mutation-sensitivity experiments."""
import unreal,pathlib,json,traceback,copy,time,hashlib,collections,re
from inventory_graph_helpers import *
VERSION='a11-paths-1'
def only_link(p):
 links=list(P.list_connected_pins(p));assert len(links)==1,('Expected one data producer',str(P.get_pin_name(p)));return links[0]
def optional_pin(n,name):
 return next((p for p in B.list_all_pins(n) if str(P.get_pin_name(p))==name),None)
def variable(n):
 ps=[p for p in B.list_all_pins(n) if str(P.get_pin_name(p)) not in ('execute','then','self','Output_Get')];assert len(ps)==1,(n.get_name(),[str(P.get_pin_name(p)) for p in ps]);return str(P.get_pin_name(ps[0]))
def analyze(bp):
 ed=G.get_graph_editor_by_name(bp,'TryTransferExact');nodes=list(ed.list_all_nodes());entry=next(n for n in nodes if n.get_class().get_name()=='K2Node_FunctionEntry');paths=[]
 def side(n):
  p=optional_pin(n,'self')
  if p is None or not P.list_connected_pins(p):return 'src'
  q=only_link(p);assert P.get_owning_node(q)==entry and str(P.get_pin_name(q))=='Destination',('Unknown target',n.get_name());return 'dst'
 allowed={'K2Node_FunctionEntry','K2Node_FunctionResult','K2Node_VariableGet','K2Node_VariableSet','K2Node_CallFunction','K2Node_CallArrayFunction','K2Node_IfThenElse','K2Node_MakeStruct','K2Node_BreakStruct','K2Node_PromotableOperator','K2Node_CommutativeAssociativeBinaryOperator','K2Node_Self'}
 owncalls={'ValidateSlots','CheckStackIdsUnique','FindStackIndex','SimulateTakeStack','SimulateReceiveStack','CheckTransferInvariants','ApplyCandidate','BroadcastChange'}
 for n in nodes:
  cls=n.get_class().get_name();assert cls in allowed,('Unsupported node',n.get_name(),cls)
  if cls=='K2Node_CallFunction':
   title=str(B.get_node_title(n));assert title in owncalls or title in ('Is Valid','IsValid','Equal (Byte)','EqualEqual_ByteByte','Equal (Object)','EqualEqual_ObjectObject','Equal (Guid)','EqualEqual_GuidGuid') or title in ('NOT Boolean','AND Boolean','OR Boolean') or re.fullmatch(r'(integer|float|double|byte|bool|object|guid)\s*(==|<=|>=|<|>|\+)\s*(integer|float|double|byte|bool|object|guid)',title,re.I),('Unsupported call',n.get_name(),title)
 def walk(n,state,path):
  assert n.get_name() not in path,('Execution cycle',n.get_name());path=path+[n.get_name()];st=copy.deepcopy(state);cls=n.get_class().get_name()
  if cls=='K2Node_VariableSet':
   name=variable(n)
   if name in ('SrcGuardBefore','DstGuardBefore'):
    expected='src' if name.startswith('Src') else 'dst';q=only_link(pin(n,name,'INPUT'));producer=P.get_owning_node(q)
    assert producer.get_class().get_name()=='K2Node_VariableGet' and str(P.get_pin_name(q))=='MutationInProgress' and side(producer)==expected,('Wrong guard snapshot',name)
    assert not st['actions'] and name not in st['snapshots'],('Guard snapshot rewritten',name);st['snapshots'].append(name)
   elif name=='MutationInProgress':
    who=side(n);p=pin(n,name,'INPUT');links=list(P.list_connected_pins(p))
    if not links:assert str(P.get_pin_value(p)).lower()=='true',('Literal guard restore',n.get_name());action=who+'=true'
    else:
     q=only_link(p);producer=P.get_owning_node(q);expected='SrcGuardBefore' if who=='src' else 'DstGuardBefore'
     assert producer.get_class().get_name()=='K2Node_VariableGet' and str(P.get_pin_name(q))==expected and expected in st['snapshots'],('Wrong restore',n.get_name(),expected);action=who+'=restored'
    st['actions'].append(action)
   else:assert name in ('DstRevision','StackIndex','SrcWeightBefore','SrcRev','DstRev'),('Unexpected variable write',name)
  if cls=='K2Node_CallFunction':
   title=str(B.get_node_title(n))
   if title in ('ApplyCandidate','BroadcastChange'):st['actions'].append(title+':'+side(n))
  if cls=='K2Node_FunctionResult':
   ex=optional_pin(n,'execute')
   q=only_link(pin(n,'Result','INPUT'));res=P.get_owning_node(q);assert res.get_class().get_name()=='K2Node_MakeStruct','Nonliteral return';success=pin(res,'Success','INPUT');assert not P.list_connected_pins(success),'Dynamic return';ok=str(P.get_pin_value(success)).lower()=='true'
   a=st['actions'];acquire=['src=true','dst=true'];restore=['src=restored','dst=restored'];apply=['ApplyCandidate:src','ApplyCandidate:dst'];broadcast=['BroadcastChange:src','BroadcastChange:dst']
   if not ok:
    kind='P1' if not a else 'P2';assert not a or a==acquire+restore,('Failure path actions',n.get_name(),a)
   else:
    kind='P3' if a==acquire+apply+restore+broadcast else 'P4';assert a in (acquire+apply+restore+broadcast,acquire+apply+restore+broadcast[:1]),('Success actions',n.get_name(),a)
    assert st.get('post_broadcast_branch')==('then' if kind=='P3' else 'else'),'Missing IsValid split'
    for field,localname in [('NewRevision','SrcRev')]:
     q=only_link(pin(res,field,'INPUT'));assert P.get_owning_node(q).get_class().get_name()=='K2Node_VariableGet' and str(P.get_pin_name(q))==localname,'Uncached source revision'
    q=only_link(pin(n,'DestinationNewRevision','INPUT'));assert str(P.get_pin_name(q))=='DstRev','Uncached destination revision'
   if a:assert sorted(st['snapshots'])==['DstGuardBefore','SrcGuardBefore'],'Missing snapshots'
   paths.append({'kind':kind,'nodes':path,'actions':a});return
  if cls=='K2Node_IfThenElse':
   if 'ApplyCandidate:src' in st['actions'] and 'dst=restored' not in st['actions']:raise AssertionError('Branch during apply/restore')
   if 'BroadcastChange:src' in st['actions']:
    q=only_link(pin(n,'Condition'));v=P.get_owning_node(q);assert str(B.get_node_title(v)) in ('Is Valid','IsValid'),'Wrong post-broadcast predicate';q=only_link(pin(v,'Object','INPUT'));assert P.get_owning_node(q)==entry and str(P.get_pin_name(q))=='Destination','Wrong IsValid target'
  exits=[p for p in B.list_all_pins(n) if 'OUTPUT' in str(P.get_pin_direction(p)) and str(P.get_pin_name(p)) in ('then','else')];assert exits,('Unsupported exec node',n.get_name(),cls)
  for p in exits:
   links=list(P.list_connected_pins(p));assert len(links)==1,('Unterminated or fanout path',n.get_name(),str(P.get_pin_name(p)))
   ss=copy.deepcopy(st)
   if cls=='K2Node_IfThenElse' and 'BroadcastChange:src' in st['actions']:ss['post_broadcast_branch']=str(P.get_pin_name(p))
   walk(P.get_owning_node(links[0]),ss,path)
 walk(entry,{'actions':[],'snapshots':[]},[])
 counts=collections.Counter(p['kind'] for p in paths);assert counts['P2']>=10 and counts['P3'] and counts['P4'],('Vacuous coverage',counts)
 # A clean graph can contain only an entirely disconnected default result.
 reached={x for p in paths for x in p['nodes']}
 for n in nodes:
  if n.get_class().get_name()=='K2Node_FunctionResult' and n.get_name() not in reached:assert not any(P.list_connected_pins(p) for p in B.list_all_pins(n)),('Missed connected return',n.get_name())
 # Every helper reachable from invariants is read-only at the component boundary.
 for helper in ['CheckTransferInvariants','CheckStackIdsUnique','CheckReceiveExact']:
  hed=G.get_graph_editor_by_name(bp,helper);localnames=set(map(str,hed.list_local_variable_names()))
  for n in hed.list_all_nodes():
   if n.get_class().get_name()=='K2Node_VariableSet':assert variable(n) in localnames,('Helper writes member',helper,n.get_name())
   if 'Call' in n.get_class().get_name():assert str(B.get_node_title(n)) not in ('ApplyCandidate','BroadcastChange','CommitInventory','New Guid','NewGuid','Delay'),('Forbidden helper call',helper,n.get_name())
 return {'version':VERSION,'passed':True,'counts':dict(counts),'paths':paths}

def bypass(n):
 inp_=pin(n,'execute');out=pin(n,'then','OUTPUT');prev=list(P.list_connected_pins(inp_));following=list(P.list_connected_pins(out));assert len(prev)==len(following)==1;P.break_pin_links(inp_);P.break_pin_links(out);wire(prev[0],following[0])
def sensitivity(original):
 # Installed UE source: AssetTools.cpp PerformDuplicateAsset saves only when SourceControl is enabled.
 # Enforce disabled SCC, use nonpersistent packages, and never call Save on duplicates.
 assert not unreal.SourceControl.is_enabled(),'Cannot safely duplicate while source control is enabled'
 results=[]
 for mutation in range(1,11):
  name='A11Sensitivity'+str(time.time_ns());bp=unreal.AssetToolsHelpers.get_asset_tools().duplicate_asset(name,'/Game/__InventoryContractTests',original);assert bp and bp!=original
  disk=pathlib.Path(unreal.Paths.project_content_dir())/'__InventoryContractTests'/(name+'.uasset');assert not disk.exists(),'Duplicate unexpectedly saved'
  ed=G.get_graph_editor_by_name(bp,'TryTransferExact');baseline=analyze(bp);nodes={n.get_name():n for n in ed.list_all_nodes()}
  p2=next(p for p in baseline['paths'] if p['kind']=='P2');p3=next(p for p in baseline['paths'] if p['kind']=='P3')
  restores=lambda p:[nodes[n] for n in p['nodes'] if nodes[n].get_class().get_name()=='K2Node_VariableSet' and optional_pin(nodes[n],'MutationInProgress') is not None and P.list_connected_pins(pin(nodes[n],'MutationInProgress','INPUT'))]
  rs=restores(p2);rt=restores(p3)
  if mutation<=4:bypass((rs+rt)[mutation-1])
  elif mutation==5:bypass(next(nodes[n] for n in p3['nodes'] if str(B.get_node_title(nodes[n]))=='ApplyCandidate' and any(str(P.get_pin_name(q))=='Destination' for q in P.list_connected_pins(pin(nodes[n],'self')))))
  elif mutation==6:
   # Swap the destination apply and source broadcast exec positions on the success path.
   applys=[nodes[n] for n in p3['nodes'] if str(B.get_node_title(nodes[n]))=='ApplyCandidate'];broadcast=next(nodes[n] for n in p3['nodes'] if str(B.get_node_title(nodes[n]))=='BroadcastChange');a=applys[1];b=broadcast
   ap=only_link(pin(a,'execute'));an=only_link(pin(a,'then','OUTPUT'));bp_=only_link(pin(b,'execute'));bn=only_link(pin(b,'then','OUTPUT'))
   for n in [a,b]:P.break_pin_links(pin(n,'execute'));P.break_pin_links(pin(n,'then','OUTPUT'))
   wire(ap,pin(b,'execute'));wire(nextpin(b),an);wire(bp_,pin(a,'execute'));wire(nextpin(a),bn)
  elif mutation in (7,8):
   n=rt[0];p=pin(n,'MutationInProgress','INPUT');P.break_pin_links(p)
   if mutation==7:lit(n,'MutationInProgress','false')
   else:wire(lg(ed,'DstGuardBefore'),p)
  else:
   prev=only_link(pin(rt[0],'execute'));P.break_pin_links(pin(rt[0],'execute'));bad=call(ed,'/Script/Engine.KismetSystemLibrary.Delay' if mutation==9 else own(bp,'CommitInventory'));wire(prev,pin(bad,'execute'));wire(nextpin(bad),pin(rt[0],'execute'))
  rejected=False;reason=''
  try:analyze(bp)
  except AssertionError as e:rejected=True;reason=str(e)
  results.append({'mutation':mutation,'rejected':rejected,'reason':reason});assert rejected,('Sensitivity miss',mutation);assert not disk.exists()
 return {'status':'PASS','mutations':results}
if __name__=='__main__':
 r={'tests':[],'passed':False};asset=pathlib.Path(unreal.Paths.project_dir())/'Content/Survival/Inventory/BPC_Inventory.uasset';before=hashlib.sha256(asset.read_bytes()).hexdigest()
 try:
  bp=unreal.load_asset('/Game/Survival/Inventory/BPC_Inventory');r['graph']=analyze(bp);r['tests'].append({'test':'33a exhaustive execution paths','passed':True});r['sensitivity']=sensitivity(bp);r['tests'].append({'test':'33b ten real unsaved mutations rejected','passed':True});r['passed']=True
 except Exception:r['error']=traceback.format_exc()
 r['sha256_before']=before;r['sha256_after']=hashlib.sha256(asset.read_bytes()).hexdigest();r['passed']=r['passed'] and before==r['sha256_after']
 pathlib.Path(__file__).with_name('a11_graph_verification.json').write_text(json.dumps(r,indent=2,ensure_ascii=False),encoding='utf-8');assert r['passed'],r.get('error')
