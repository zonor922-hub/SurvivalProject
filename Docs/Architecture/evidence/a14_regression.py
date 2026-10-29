import unreal,sys,pathlib,json,time,traceback
root=pathlib.Path(__file__).resolve().parents[3];sys.path.insert(0,str(root/'Docs/Architecture/evidence'))
r={'tests':[],'passed':False};s={'start':time.monotonic()}
def check(n,v,d=None):
 r['tests'].append({'name':n,'passed':bool(v),'detail':d});assert v,(n,d)
def save(): (root/'Saved/a14_regression.json').write_text(json.dumps(r,indent=2,default=str),encoding='utf-8')
try:
 from a12_suite import suite
 gi=unreal.new_object(unreal.load_asset('/Game/Survival/Core/BP_SurvivalGameInstance').generated_class());gi.call_method('InitializeCatalog');bp=unreal.load_asset('/Game/Survival/Inventory/BPC_Inventory')
 r['a12_tests']=[]
 for scenario in [1,2,3]:suite(gi,bp,scenario,r['a12_tests'])
 unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).load_level('/Game/Survival/Maps/LV_SystemsTest')
except:r['error']=traceback.format_exc();save();unreal.SystemLibrary.quit_editor();raise

def run():
 unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).editor_request_begin_play()
 for _ in range(70):yield
 world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world();pc=unreal.GameplayStatics.get_player_controller(world,0);pawn=pc.get_controlled_pawn()
 modes={v.value:v for v in [getattr(type(pc.get_editor_property('CurrentInputMode')),k) for k in dir(type(pc.get_editor_property('CurrentInputMode')))] if isinstance(v,type(pc.get_editor_property('CurrentInputMode')))}
 sub=next(s for s in unreal.ObjectIterator(unreal.EnhancedInputLocalPlayerSubsystem) if isinstance(s.get_outer(),unreal.LocalPlayer));jump=unreal.load_asset('/Game/Input/Actions/IA_Jump')
 for mode in [0,1,2,0]:
  pc.call_method('SetSurvivalInputMode',(modes[mode],))
  for _ in range(90):yield
  start=pawn.get_actor_location().z;peak=0
  for i in range(40):
   sub.inject_input_vector_for_action(jump,unreal.Vector(1 if i<5 else 0,0,0),[],[])
   yield
   peak=max(peak,pawn.get_actor_location().z-start)
  check('Jump policy mode '+str(mode),peak<1 if mode==1 else peak>10,peak)
 r['passed']=True
 unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).editor_request_end_play()
 for _ in range(15):yield
gen=run()
def tick(dt):
 try:
  assert time.monotonic()-s['start']<120
  next(gen)
 except StopIteration:
  save();unreal.unregister_slate_post_tick_callback(s['handle']);unreal.SystemLibrary.quit_editor()
 except:
  r['error']=traceback.format_exc();save();unreal.unregister_slate_post_tick_callback(s['handle']);unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).editor_request_end_play();unreal.SystemLibrary.quit_editor()
s['handle']=unreal.register_slate_post_tick_callback(tick)
