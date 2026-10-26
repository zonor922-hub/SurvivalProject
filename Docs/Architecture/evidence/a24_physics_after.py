"""A24 physical motion and above-surface mode probe on a transient owned pawn."""
import unreal,json,pathlib,time,traceback
_a24p={'phase':'start','started':time.monotonic(),'frame':0,'samples':[]};_a24pout=pathlib.Path(__file__).resolve().with_name('a24_physics_after.json');_a24ped=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem);_a24plev=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
def _a24pfinish(ok):
 _a24p['success']=ok;_a24pout.write_text(json.dumps({k:v for k,v in _a24p.items() if k not in ('handle','started','pawn')},indent=2),encoding='utf-8');unreal.unregister_slate_post_tick_callback(_a24p['handle'])
 globals()['_a24_job_result']=ok
def _a24ptick(dt):
 try:
  _a24p['frame']+=1;w=_a24ped.get_game_world();assert time.monotonic()-_a24p['started']<180
  if _a24p['phase']=='start':
   assert w is None;_a24plev.editor_request_begin_play();_a24p['phase']='spawn';return
  if _a24p['phase']=='end':
   if w is None:_a24pfinish(True)
   return
  if not w:return
  if _a24p['phase']=='spawn' and _a24p['frame']<15:return
  pc=unreal.GameplayStatics.get_player_controller(w,0)
  if _a24p['phase']=='spawn':
   old=unreal.GameplayStatics.get_player_pawn(w,0);cls=unreal.load_asset('/Game/Survival/Character/BP_SurvivalCharacter').generated_class();t=unreal.Transform(location=unreal.Vector(11000,18000,-180));g=unreal.get_default_object(unreal.GameplayStatics)
   pawn=g.call_method('BeginDeferredActorSpawnFromClass',(w,cls,t,unreal.SpawnActorCollisionHandlingMethod.ALWAYS_SPAWN,None,unreal.SpawnActorScaleMethod.MULTIPLY_WITH_ROOT));pawn=g.call_method('FinishSpawningActor',(pawn,t,unreal.SpawnActorScaleMethod.MULTIPLY_WITH_ROOT));pc.possess(pawn);old.destroy_actor();_a24p['pawn']=pawn;_a24p['phase']='rise';_a24p['since']=unreal.GameplayStatics.get_time_seconds(w);_a24p['initial_z']=pawn.get_actor_location().z;pc.set_control_rotation(unreal.Rotator(pitch=45,yaw=0,roll=0));return
  pawn=_a24p['pawn'];move=pawn.get_component_by_class(unreal.CharacterMovementComponent);elapsed=unreal.GameplayStatics.get_time_seconds(w)-_a24p['since']
  if _a24p['phase'] in ('rise','descend'):
   pawn.call_method('Move',(0.0,1.0))
   if elapsed<1.5:return
   loc=pawn.get_actor_location();_a24p['samples'].append({'phase':_a24p['phase'],'delta_z':loc.z-_a24p['initial_z'],'location':list(loc.to_tuple()),'mode':str(move.get_editor_property('movement_mode'))})
   assert (loc.z-_a24p['initial_z']>50 if _a24p['phase']=='rise' else loc.z-_a24p['initial_z']< -50),'Vertical swimming failed'
   if _a24p['phase']=='rise':
    pc.set_control_rotation(unreal.Rotator(pitch=-45,yaw=0,roll=0));move.stop_movement_immediately();pawn.consume_movement_input_vector();_a24p['phase']='descend';_a24p['initial_z']=loc.z;_a24p['since']=unreal.GameplayStatics.get_time_seconds(w);return
   pawn.set_actor_location(unreal.Vector(11000,18000,150),False,True);move.stop_movement_immediately();move.set_movement_mode(unreal.MovementMode.MOVE_FALLING);_a24p['phase']='air';_a24p['frame']=0;return
  if _a24p['phase']=='air':
   if _a24p['frame']<2:return
   assert move.get_editor_property('movement_mode')!=unreal.MovementMode.MOVE_SWIMMING,'Swimming above water';_a24p['samples'].append({'phase':'above water','location':list(pawn.get_actor_location().to_tuple()),'mode':str(move.get_editor_property('movement_mode'))});_a24plev.editor_request_end_play();_a24p['phase']='end'
 except Exception:
  _a24p['error']=traceback.format_exc()
  if _a24ped.get_game_world():_a24plev.editor_request_end_play()
  _a24pfinish(False)
assert _a24plev.load_level('/Game/Content/Survival/Maps/LV_Survival_Nature')
_a24p['handle']=unreal.register_slate_post_tick_callback(_a24ptick)
