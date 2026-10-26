import unreal,json,pathlib,time,traceback
_a8={'phase':'start','frame':0,'runs':[],'started':time.monotonic()};_a8out=pathlib.Path(__file__).resolve().with_name('a08_pie.json');_a8ed=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem);_a8lev=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
def _a8finish(ok):
 _a8['passed']=ok;_a8out.write_text(json.dumps({k:v for k,v in _a8.items() if k not in ('handle','started')},indent=2),encoding='utf-8');unreal.unregister_slate_post_tick_callback(_a8['handle'])
 unreal.EditorPythonScripting.set_keep_python_script_alive(False)
def _a8tick(dt):
 try:
  _a8['frame']+=1;w=_a8ed.get_game_world();assert time.monotonic()-_a8['started']<120
  if _a8['phase']=='start':
   assert w is None;_a8lev.editor_request_begin_play();_a8['phase']='run';_a8['frame']=0;return
  if _a8['phase']=='run':
   if w is None or _a8['frame']<60:return
   gi=unreal.GameplayStatics.get_game_instance(w);pc=unreal.GameplayStatics.get_player_controller(w,0);assert gi.get_editor_property('CatalogReady') and pc.get_editor_property('BootstrapReady');assert len(gi.get_editor_property('ItemDefinitions'))==4
   ps=pc.get_editor_property('player_state');inv=ps.get_component_by_class(unreal.load_asset('/Game/Survival/Inventory/BPC_Inventory').generated_class());assert inv and inv.get_editor_property('Initialized');assert inv.call_method('GetCurrentWeight')==(0.0,True);assert len(inv.get_editor_property('Slots'))==4;assert not inv.is_component_tick_enabled();assert ps.get_editor_property('BootstrapReady');assert 'ABP_Survival' in unreal.GameplayStatics.get_player_pawn(w,0).get_component_by_class(unreal.SkeletalMeshComponent).get_anim_instance().get_class().get_path_name()
   _a8['runs'].append({'catalog_ready':True,'pc_ready':True,'count':4,'inventory_initialized':True,'inventory_weight':0,'inventory_tick_enabled':False,'gi_initialize_count':gi.get_editor_property('InitializeCount')});_a8lev.editor_request_end_play();_a8['phase']='end';return
  if _a8['phase']=='end':
   if w:return
   if len(_a8['runs'])==3:_a8finish(True)
   else:_a8['phase']='start'
 except Exception:
  _a8['error']=traceback.format_exc()
  if _a8ed.get_game_world():_a8lev.editor_request_end_play()
  _a8finish(False)
assert _a8lev.load_level('/Game/Survival/Maps/LV_SystemsTest')
_a8['handle']=unreal.register_slate_post_tick_callback(_a8tick)
