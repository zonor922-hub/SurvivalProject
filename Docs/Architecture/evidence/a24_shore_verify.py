"""A24: continuous shore entry/exit at three locations, on the owned pawn."""
import unreal,json,pathlib,time,traceback,math
_a24s={'phase':'start','frame':0,'started':time.monotonic(),'shore':0,'leg':0,'runs':[],'changes':[]};_a24sout=pathlib.Path(__file__).resolve().with_name('a24_shore_verification.json');_a24sed=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem);_a24slev=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
_a24shores=[('west',(5800,17000),(7800,17200)),('east',(14100,18000),(12500,18000)),('south',(11300,13000),(11300,15100))]
def _a24sfinish(ok):
 _a24s['passed']=ok;_a24sout.write_text(json.dumps({k:v for k,v in _a24s.items() if k not in ('handle','started','pawn')},indent=2),encoding='utf-8');unreal.unregister_slate_post_tick_callback(_a24s['handle'])
 globals()['_a24_job_result']=ok
def _a24stick(dt):
 try:
  _a24s['frame']+=1;w=_a24sed.get_game_world();assert time.monotonic()-_a24s['started']<300
  if _a24s['phase']=='start':
   assert not w;_a24slev.editor_request_begin_play();_a24s['phase']='spawn';return
  if _a24s['phase']=='end':
   if not w:_a24sfinish(True)
   return
  if not w:return
  pc=unreal.GameplayStatics.get_player_controller(w,0)
  if _a24s['phase']=='spawn':
   if _a24s['frame']<15:return
   old=unreal.GameplayStatics.get_player_pawn(w,0);g=unreal.get_default_object(unreal.GameplayStatics);t=old.get_actor_transform();cls=unreal.load_asset('/Game/Survival/Character/BP_SurvivalCharacter').generated_class();pawn=g.call_method('BeginDeferredActorSpawnFromClass',(w,cls,t,unreal.SpawnActorCollisionHandlingMethod.ALWAYS_SPAWN,None,unreal.SpawnActorScaleMethod.MULTIPLY_WITH_ROOT));pawn=g.call_method('FinishSpawningActor',(pawn,t,unreal.SpawnActorScaleMethod.MULTIPLY_WITH_ROOT));pc.possess(pawn);old.destroy_actor();_a24s['pawn']=pawn;_a24s['phase']='place'
  pawn=_a24s['pawn'];move=pawn.get_component_by_class(unreal.CharacterMovementComponent);label,outside,inside=_a24shores[_a24s['shore']]
  if _a24s['phase']=='place':
   x,y=outside;hit=unreal.SystemLibrary.line_trace_single(w,unreal.Vector(x,y,3000),unreal.Vector(x,y,-4000),unreal.TraceTypeQuery.ECC_VISIBILITY,False,[pawn],unreal.DrawDebugTrace.NONE,True);import re;z=float(re.search(r'ImpactPoint=\(X=[^,]+,Y=[^,]+,Z=([^\)]+)',hit.export_text()).group(1));pawn.set_actor_location(unreal.Vector(x,y,z+100),False,True);move.stop_movement_immediately();pawn.consume_movement_input_vector();_a24s['phase']='settle';_a24s['since']=unreal.GameplayStatics.get_time_seconds(w);_a24s['leg']=0;return
  now=unreal.GameplayStatics.get_time_seconds(w)
  if _a24s['phase']=='settle':
   if now-_a24s['since']<0.5:return
   assert move.get_editor_property('movement_mode')==unreal.MovementMode.MOVE_WALKING
   _a24s['phase']='travel';_a24s['since']=now;_a24s['last_mode']='';_a24s['changes']=[]
  if _a24s['phase']=='travel':
   target=inside if _a24s['leg']==0 else outside;loc=pawn.get_actor_location();mode=str(move.get_editor_property('movement_mode'))
   if mode!=_a24s['last_mode']:_a24s['changes'].append(mode);_a24s['last_mode']=mode
   distance=math.hypot(loc.x-target[0],loc.y-target[1]);assert now-_a24s['since']<18,(label,_a24s['leg'],distance,mode)
   if distance<100:
    expected=unreal.MovementMode.MOVE_SWIMMING if _a24s['leg']==0 else unreal.MovementMode.MOVE_WALKING;assert move.get_editor_property('movement_mode')==expected,(label,mode)
    anim=pawn.get_component_by_class(unreal.SkeletalMeshComponent).get_anim_instance();assert bool(anim.get_editor_property('IsSwimming'))==(_a24s['leg']==0),'Animation mode mismatch';_a24s['runs'].append({'shore':label,'leg':'entry' if _a24s['leg']==0 else 'exit','mode':mode,'changes':list(_a24s['changes']),'swim_animation':bool(anim.get_editor_property('IsSwimming')),'location':list(loc.to_tuple())});move.stop_movement_immediately();pawn.consume_movement_input_vector()
    if _a24s['leg']==0:_a24s['leg']=1;_a24s['since']=now;_a24s['last_mode']='';_a24s['changes']=[];return
    _a24s['shore']+=1
    if _a24s['shore']>=len(_a24shores):_a24slev.editor_request_end_play();_a24s['phase']='end'
    else:_a24s['phase']='place'
    return
   pc.set_control_rotation(unreal.MathLibrary.find_look_at_rotation(loc,unreal.Vector(target[0],target[1],loc.z)));pawn.call_method('Move',(0.0,1.0))
 except Exception:
  _a24s['error']=traceback.format_exc()
  if _a24sed.get_game_world():_a24slev.editor_request_end_play()
  _a24sfinish(False)
assert _a24slev.load_level('/Game/Content/Survival/Maps/LV_Survival_Nature');_a24s['handle']=unreal.register_slate_post_tick_callback(_a24stick)
