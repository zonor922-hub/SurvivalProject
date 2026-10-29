import unreal,sys,json,pathlib,time,traceback
root=pathlib.Path(__file__).resolve().parents[3];sys.path.insert(0,str(root/'Docs/Architecture/evidence'))
from inventory_graph_helpers import *
import runpy
runpy.run_path(str(pathlib.Path(__file__).with_name('a14_blueprint_audit.py')))
report={'engine':unreal.SystemLibrary.get_engine_version(),'tests':[],'compile':{},'passed':False,'mode':'real PIE with Enhanced Input action injection'}
state={'started':time.monotonic(),'frame':0};refs=[]
def check(name,ok,detail=None):
 report['tests'].append({'name':name,'passed':bool(ok),'detail':detail})
 assert ok,(name,detail)
def save():
 (root/'Saved/a14_pie.json').write_text(json.dumps(report,ensure_ascii=False,indent=2,default=str),encoding='utf-8')
def listener(pc_bp):
 bp=B.create_blueprint_asset_with_parent('/Game/__A14Tests/Listener'+str(time.time_ns()),unreal.Object);refs.append(bp)
 for name,typ,default in [('InteractCount',basic('int'),'0'),('ModeCount',basic('int'),'0'),('LastPawn',B.get_object_reference_type(unreal.Pawn.static_class()),'')]:var(bp,name,typ,default)
 for fn,param,typ,count in [('ReceiveInteract','Pawn',B.get_object_reference_type(unreal.Pawn.static_class()),'InteractCount'),('ReceiveMode','Mode',B.get_member_variable_type(pc_bp,'CurrentInputMode'),'ModeCount')]:
  ed=graph(bp,fn);p=ed.add_graph_input_parameter(param,typ);entry=member(ed,count,math(ed,'Add_IntInt',get(ed,count),1),ed.find_graph_entry_pin())
  if param=='Pawn':member(ed,'LastPawn',p,entry)
 assert B.compile_blueprint(bp)
 ed=graph(bp,'Bind');target=ed.add_graph_input_parameter('Target',B.get_object_reference_type(pc_bp.generated_class()));entry=ed.find_graph_entry_pin()
 for dispatcher,fn in [('OnInteractRequested','ReceiveInteract'),('OnSurvivalInputModeChanged','ReceiveMode')]:
  act=next(str(a) for a in ed.list_available_nodes([target]) if str(a).endswith('|BindEventto'+dispatcher));bind=ed.create_node_from_name(act,unreal.Vector2D(0,0),[target]);wire(target,pin(bind,'self'));wire(entry,pin(bind,'execute'));entry=value(bind,'then')
  dp=pin(bind,'Delegate');act=next(str(a) for a in ed.list_available_nodes([dp]) if str(a).endswith('|Создатьсобытие') or str(a).endswith('|CreateEvent'));d=ed.create_node_from_name(act,unreal.Vector2D(0,0),[dp]);wire(next(p for p in B.list_all_pins(d) if 'OUTPUT' in str(P.get_pin_direction(p))),dp);B.set_create_delegate_function(d,fn)
 assert B.compile_blueprint(bp);return bp
try:
 pc_bp=unreal.load_asset('/Game/Survival/Core/BP_SurvivalPlayerController')
 for path in ['/Game/Survival/Core/BP_SurvivalPlayerController','/Game/Survival/Core/BP_SurvivalGameMode','/Game/Survival/Core/BP_SurvivalGameInstance','/Game/Survival/Core/BP_SurvivalPlayerState','/Game/Survival/Character/BP_SurvivalCharacter','/Game/Survival/Interaction/BPC_Interaction','/Game/Survival/Interaction/BPI_Interactable','/Game/Survival/Inventory/BPC_Inventory']:
  bp=unreal.load_asset(path);report['compile'][path]={'passed':B.compile_blueprint(bp),'status':str(bp.get_editor_property('status'))};assert report['compile'][path]['passed']
 lbp=listener(pc_bp)
 imc=unreal.load_asset('/Game/Survival/Input/IMC_Survival');report['mappings']=[{'action':m.action.get_name(),'key':str(m.key.export_text())} for m in imc.default_key_mappings.mappings]
 unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).load_level('/Game/Survival/Maps/LV_SystemsTest')
except:
 report['error']=traceback.format_exc();save();unreal.SystemLibrary.quit_editor();raise

def run():
 for launch in range(2):
  unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).editor_request_begin_play()
  for _ in range(30):yield
  world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world();assert world
  pc=unreal.GameplayStatics.get_player_controller(world,0);assert pc.get_class()==pc_bp.generated_class(),pc
  li=unreal.new_object(lbp.generated_class());refs.append(li);li.call_method('Bind',(pc,))
  sub=next(s for s in unreal.ObjectIterator(unreal.EnhancedInputLocalPlayerSubsystem) if isinstance(s.get_outer(),unreal.LocalPlayer))
  actions={n:unreal.load_asset('/Game/Survival/Input/Actions/'+n) for n in ['IA_Interact','IA_Inventory']}
  def count():return li.get_editor_property('InteractCount')
  modes={v.value:v for v in [getattr(type(pc.get_editor_property('CurrentInputMode')),k) for k in dir(type(pc.get_editor_property('CurrentInputMode')))] if isinstance(v,type(pc.get_editor_property('CurrentInputMode')))};report['enum_values']={k:str(v) for k,v in modes.items()}
  def mode():return pc.get_editor_property('CurrentInputMode').value
  def policy(m):return mode()==m and pc.is_move_input_ignored()==(m==1) and pc.is_look_input_ignored()==(m==1) and pc.get_editor_property('show_mouse_cursor')==(m==1)
  def press(name,frames=8):
   for _ in range(frames):sub.inject_input_vector_for_action(actions[name],unreal.Vector(1,0,0),[],[]);yield
   for _ in range(4):sub.inject_input_vector_for_action(actions[name],unreal.Vector(0,0,0),[],[]);yield
  check('PIE %s bootstrap ready'%launch,pc.get_editor_property('BootstrapReady'))
  check('PIE %s default policy'%launch,policy(0))
  raw=sub.has_mapping_context(imc);report.setdefault('context_results',[]).append({'context':'IMC_Survival','raw':str(raw)});check('survival context present',raw is not None)
  old=count();yield from press('IA_Interact',15);check('held Interact emits once',count()==old+1)
  check('Interact carries current Pawn',li.get_editor_property('LastPawn')==pc.get_controlled_pawn())
  for base in [0,2]:
   pc.call_method('SetSurvivalInputMode',(modes[base],));check('base mode policy '+str(base),policy(base))
   for cycle in range(10):
    before=li.get_editor_property('ModeCount');yield from press('IA_Inventory',5)
    check('Tab opens UI base%s cycle%s'%(base,cycle),policy(1))
    check('held Tab changes mode once',li.get_editor_property('ModeCount')==before+1)
    for _ in range(3):pc.call_method('SetSurvivalInputMode',(modes[1],))
    check('repeated UI mode is idempotent',li.get_editor_property('ModeCount')==before+1)
    old=count();yield from press('IA_Interact',4);check('UI blocks Interact',count()==old)
    yield from press('IA_Inventory',5);check('Tab restores previous mode',policy(base))
   old=count();yield from press('IA_Interact',5);check('mode Interact policy '+str(base),count()==old+(1 if base==0 else 0))
  # All direct transitions, including repeated UI, must never accumulate locks.
  for a,b in [(2,1),(1,2),(2,0),(0,1),(1,0),(0,2)]:
   pc.call_method('SetSurvivalInputMode',(modes[a],));pc.call_method('SetSurvivalInputMode',(modes[b],));check('direct transition %s->%s'%(a,b),policy(b))
  ps=pc.get_editor_property('player_state');inv=ps.get_component_by_class(unreal.load_asset('/Game/Survival/Inventory/BPC_Inventory').generated_class());snap=inv.call_method('GetSnapshot').export_text()
  generation=pc.get_editor_property('PossessionGeneration')
  additions=[]
  def added(ctx):additions.append(ctx.get_path_name())
  sub.on_mapping_context_added.add_callable(added)
  for swap in range(3):
   pc.call_method('SetSurvivalInputMode',(modes[1 if swap!=1 else 2],));oldpawn=pc.get_controlled_pawn();pc.un_possess()
   old=count();yield from press('IA_Interact',4);yield from press('IA_Inventory',4)
   check('unpossessed commands blocked',count()==old and not pc.get_editor_property('BootstrapReady'))
   transform=unreal.Transform(location=unreal.Vector(swap*300,0,300));pawn=unreal.get_default_object(unreal.GameplayStatics).call_method('BeginDeferredActorSpawnFromClass',(world,unreal.load_asset('/Game/Survival/Character/BP_SurvivalCharacter').generated_class(),transform,unreal.SpawnActorCollisionHandlingMethod.ALWAYS_SPAWN,None,unreal.SpawnActorScaleMethod.MULTIPLY_WITH_ROOT));unreal.get_default_object(unreal.GameplayStatics).call_method('FinishSpawningActor',(pawn,transform,unreal.SpawnActorScaleMethod.MULTIPLY_WITH_ROOT))
   pc.possess(pawn)
   for _ in range(5):yield
   check('swap %s resets policy'%swap,policy(0))
   check('swap %s bootstrap rebound'%swap,pc.get_editor_property('BootstrapReady') and pc.get_editor_property('BoundPawn')==pawn and pc.get_editor_property('PossessionGeneration')==generation+swap+1)
   check('PlayerState and inventory survive',pc.get_editor_property('player_state')==ps and inv.call_method('GetSnapshot').export_text()==snap)
   old=count();yield from press('IA_Interact',10);check('swap %s one command, new Pawn'%swap,count()==old+1 and li.get_editor_property('LastPawn')==pawn)
   check('swap %s no mapping additions'%swap,len(additions)==0)
   oldpawn.destroy_actor()
  sub.on_mapping_context_added.remove_callable(added)
  # Template contexts and injected movement/look/jump regressions.
  for context in ['/Game/Input/IMC_Default','/Game/Input/IMC_MouseLook']:
   asset=unreal.load_asset(context);raw=sub.has_mapping_context(asset);report.setdefault('context_results',[]).append({'context':context,'raw':str(raw)});check('template context '+context,asset is not None and (raw is not None))
  pawn=pc.get_controlled_pawn();pawn.get_component_by_class(unreal.CharacterMovementComponent).set_movement_mode(unreal.MovementMode.MOVE_WALKING)
  start=pawn.get_actor_location();rot=pc.get_control_rotation()
  move=unreal.load_asset('/Game/Input/Actions/IA_Move');look=unreal.load_asset('/Game/Input/Actions/IA_MouseLook')
  for _ in range(20):
   sub.inject_input_vector_for_action(move,unreal.Vector(0,1,0),[],[]);sub.inject_input_vector_for_action(look,unreal.Vector(1,0,0),[],[]);yield
  check('template movement restored',(pawn.get_actor_location()-start).length()>1)
  check('template camera restored',pc.get_control_rotation()!=rot)
  unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).editor_request_end_play()
  for _ in range(15):yield
 report['passed']=True

gen=run()
def tick(dt):
 try:
  assert time.monotonic()-state['started']<240,'PIE watchdog timeout'
  next(gen)
 except StopIteration:
  save();unreal.unregister_slate_post_tick_callback(state['handle']);unreal.SystemLibrary.quit_editor()
 except:
  report['error']=traceback.format_exc();save();unreal.unregister_slate_post_tick_callback(state['handle']);unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).editor_request_end_play();unreal.SystemLibrary.quit_editor()
state['handle']=unreal.register_slate_post_tick_callback(tick)
