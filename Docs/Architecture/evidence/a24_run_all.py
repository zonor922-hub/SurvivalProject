"""Run isolated editor/PIE swimming checks via -ExecutePythonScript; never save assets."""
import unreal, pathlib, json, traceback, time
folder=pathlib.Path(__file__).resolve().parent
summary={'engine_version':unreal.SystemLibrary.get_engine_version(),'project_directory':unreal.Paths.project_dir(),'compile':{},'jobs':[]}
try:
 registry=unreal.AssetRegistryHelpers.get_asset_registry();registry.search_all_assets(True)
 forbidden=registry.get_assets_by_path('/Game/Survival/Inventory',recursive=True);assert len(forbidden)==0,'A08 assets present'
 for asset in registry.get_assets_by_path('/Game/Survival',recursive=True):
  bp=asset.get_asset()
  if isinstance(bp,unreal.Blueprint):
   assert unreal.BlueprintEditorLibrary.compile_blueprint(bp),bp.get_path_name()
   status=str(bp.get_editor_property('status'));summary['compile'][bp.get_path_name()]=status;assert 'BS_UP_TO_DATE' in status
 levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem);assert levels.load_level('/Game/Content/Survival/Maps/LV_Survival_Nature')
 volumes=[a for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors() if isinstance(a,unreal.PhysicsVolume) and a.get_actor_label().startswith('LakeSwimVolume')]
 summary['water_volumes']=len(volumes);assert len(volumes)==257
 for volume in volumes:
  center,extent=volume.get_actor_bounds(False);assert abs(center.z+extent.z)<0.1 and abs(center.z-extent.z+450)<0.1
  assert volume.get_editor_property('water_volume') and volume.get_editor_property('priority')==10
 summary['volume_top_z']=0;summary['volume_bottom_z']=-450
except Exception:
 summary['passed']=False;summary['error']=traceback.format_exc();(folder/'a24_verification.json').write_text(json.dumps(summary,indent=2),encoding='utf-8');raise

jobs=['a24_move_verify.py','a24_physics_after.py','a24_shore_verify.py']
state={'index':0,'active':False,'started':time.monotonic()}
unreal.EditorPythonScripting.set_keep_python_script_alive(True)
def finish(ok):
 summary['passed']=ok
 (folder/'a24_verification.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
 unreal.unregister_slate_post_tick_callback(state['handle'])
 unreal.EditorPythonScripting.set_keep_python_script_alive(False)
def tick(dt):
 try:
  assert time.monotonic()-state['started']<600,'Suite timeout'
  if state['active']:
   if '_a24_job_result' not in globals():return
   ok=globals().pop('_a24_job_result');summary['jobs'].append({'script':jobs[state['index']],'passed':ok})
   assert ok,jobs[state['index']]
   state['index']+=1;state['active']=False
   return
  if unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world():return
  if state['index']==len(jobs):finish(True);return
  script=folder/jobs[state['index']];globals()['__file__']=str(script);state['active']=True
  exec(compile(script.read_text(encoding='utf-8'),str(script),'exec'),globals())
 except Exception:
  summary['error']=traceback.format_exc()
  unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).editor_request_end_play()
  finish(False)
state['handle']=unreal.register_slate_post_tick_callback(tick)
