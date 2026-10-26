import unreal,json,pathlib,time,traceback
_a6={'phase':'start','frame':0,'runs':[],'started':time.monotonic()};_a6out=pathlib.Path(__file__).resolve().with_name('a06_pie.json');_a6ed=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem);_a6lev=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
def _a6finish(ok):
 _a6['passed']=ok;_a6out.write_text(json.dumps({k:v for k,v in _a6.items() if k not in ('handle','started')},indent=2),encoding='utf-8');unreal.unregister_slate_post_tick_callback(_a6['handle'])
 if globals().get('_a6_headless',False):unreal.EditorPythonScripting.set_keep_python_script_alive(False)
def _a6tick(dt):
 try:
  _a6['frame']+=1;w=_a6ed.get_game_world();assert time.monotonic()-_a6['started']<120
  if _a6['phase']=='start':
   assert w is None;_a6lev.editor_request_begin_play();_a6['phase']='run';_a6['frame']=0;return
  if _a6['phase']=='run':
   if w is None or _a6['frame']<60:return
   gi=unreal.GameplayStatics.get_game_instance(w);pc=unreal.GameplayStatics.get_player_controller(w,0);assert gi.get_editor_property('CatalogReady') and pc.get_editor_property('BootstrapReady');assert len(gi.get_editor_property('ItemDefinitions'))==4
   for ident in ('item.wood','item.stone','item.berry','item.plank'):assert gi.call_method('FindItemDefinition',(ident,))[1]
   assert gi.call_method('FindItemDefinition',('item.unknown',))==(None,False)
   gi.call_method('InitializeCatalog');gi.call_method('InitializeBootstrap')
   assert gi.get_editor_property('InitializeCount')==1 and len(gi.get_editor_property('ItemDefinitions'))==4
   _a6['runs'].append({'catalog_ready':True,'pc_ready':True,'count':4,'gi_initialize_count':gi.get_editor_property('InitializeCount')});_a6lev.editor_request_end_play();_a6['phase']='end';return
  if _a6['phase']=='end':
   if w:return
   if len(_a6['runs'])==3:_a6finish(True)
   else:_a6['phase']='start'
 except Exception:
  _a6['error']=traceback.format_exc()
  if _a6ed.get_game_world():_a6lev.editor_request_end_play()
  _a6finish(False)
assert _a6lev.load_level('/Game/Survival/Maps/LV_SystemsTest')
_a6['handle']=unreal.register_slate_post_tick_callback(_a6tick)
