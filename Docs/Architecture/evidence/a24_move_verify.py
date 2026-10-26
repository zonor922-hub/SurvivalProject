"""A24 input contract on the owned pawn in a transient PIE world."""
import unreal,json,pathlib,time,traceback
_a24m={'phase':'start','frame':0,'tests':[],'started':time.monotonic()};_a24mout=pathlib.Path(__file__).resolve().with_name('a24_move_verification.json');_a24med=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem);_a24mlev=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
def _a24mfinish(ok):
 _a24m['passed']=ok;_a24mout.write_text(json.dumps({k:v for k,v in _a24m.items() if k not in ('handle','started')},indent=2),encoding='utf-8');unreal.unregister_slate_post_tick_callback(_a24m['handle'])
 globals()['_a24_job_result']=ok
def _a24mtick(dt):
 try:
  _a24m['frame']+=1;w=_a24med.get_game_world();assert time.monotonic()-_a24m['started']<120
  if _a24m['phase']=='start':
   assert w is None;_a24mlev.editor_request_begin_play();_a24m['phase']='test';return
  if _a24m['phase']=='end':
   if w is None:_a24mfinish(True)
   return
  if not w or _a24m['frame']<30:return
  controller=unreal.GameplayStatics.get_player_controller(w,0);pawn=unreal.GameplayStatics.get_player_pawn(w,0);assert 'BP_SurvivalCharacter' in pawn.get_class().get_path_name();movement=pawn.get_component_by_class(unreal.CharacterMovementComponent)
  now=unreal.GameplayStatics.get_time_seconds(w)
  if _a24m['phase']=='walk':
   pawn.call_method('Move',(0.0,1.0))
   if now-_a24m['since']<0.5:return
   loc=pawn.get_actor_location();distance=(loc-unreal.Vector(*_a24m['walk_start'])).length()
   assert distance>20 and movement.get_editor_property('movement_mode')==unreal.MovementMode.MOVE_WALKING,(distance,loc)
   _a24m['tests'].append({'test':'physical dry walking','passed':True,'distance_cm':distance});movement.stop_movement_immediately();pawn.consume_movement_input_vector();_a24m['jump_z']=loc.z;pawn.jump();_a24m['since']=now;_a24m['phase']='jump';return
  if _a24m['phase']=='jump':
   if now-_a24m['since']<0.3:return
   pawn.stop_jumping();rise=pawn.get_actor_location().z-_a24m['jump_z'];assert rise>20 and movement.get_editor_property('movement_mode')==unreal.MovementMode.MOVE_FALLING,rise
   _a24m['tests'].append({'test':'physical dry jump','passed':True,'rise_cm':rise});_a24m['since']=now;_a24m['phase']='land';return
  if _a24m['phase']=='land':
   assert now-_a24m['since']<5,'Jump did not land'
   if movement.get_editor_property('movement_mode')!=unreal.MovementMode.MOVE_WALKING:return
   _a24m['tests'].append({'test':'jump returns to walking','passed':True});_a24mlev.editor_request_end_play();_a24m['phase']='end';return
  for label,mode,pitch,x,y,expected in [('swim ascend',unreal.MovementMode.MOVE_SWIMMING,45,0,1,'up'),('swim descend',unreal.MovementMode.MOVE_SWIMMING,-45,0,1,'down'),('dry pitch ignored',unreal.MovementMode.MOVE_WALKING,45,0,1,'flat'),('swim strafe',unreal.MovementMode.MOVE_SWIMMING,45,1,0,'right')]:
   movement.set_movement_mode(mode);controller.set_control_rotation(unreal.Rotator(pitch=pitch,yaw=0,roll=0));pawn.consume_movement_input_vector();pawn.call_method('Move',(float(x),float(y)));v=pawn.get_pending_movement_input_vector()
   ok=(v.z>0.7 if expected=='up' else v.z< -0.7 if expected=='down' else abs(v.z)<1e-5 and v.x>0.99 if expected=='flat' else abs(v.z)<1e-5 and v.y>0.99)
   _a24m['tests'].append({'test':label,'passed':ok,'pending_input':list(v.to_tuple()),'mode':str(movement.get_editor_property('movement_mode')),'control_rotation':str(controller.get_control_rotation()),'pawn_control_rotation':str(pawn.get_control_rotation())});assert ok,label
  movement.stop_movement_immediately();pawn.consume_movement_input_vector();movement.set_movement_mode(unreal.MovementMode.MOVE_WALKING);controller.set_control_rotation(unreal.Rotator(pitch=45,yaw=0,roll=0));_a24m['walk_start']=list(pawn.get_actor_location().to_tuple());_a24m['since']=now;_a24m['phase']='walk'
 except Exception:
  _a24m['error']=traceback.format_exc()
  if _a24med.get_game_world():_a24mlev.editor_request_end_play()
  _a24mfinish(False)
assert _a24mlev.load_level('/Game/Survival/Maps/LV_SystemsTest')
_a24m['handle']=unreal.register_slate_post_tick_callback(_a24mtick)
