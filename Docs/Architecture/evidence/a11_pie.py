"""A11 real PIE: actual PlayerState inventory and unsaved second component, 3 sessions."""
import unreal,pathlib,json,time,traceback
from a09_verify import read,write,snapshot,result,items
from a11_event_fixture import listener_class
_a11={'phase':'start','frames':0,'runs':[],'started':time.monotonic()}
_a11ed=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem);_a11lev=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
_a11bp=unreal.load_asset('/Game/Survival/Inventory/BPC_Inventory');_a11listener=listener_class(_a11bp);_a11out=pathlib.Path(__file__).with_name('a11_pie.json')
def _a11finish(ok):
 _a11['passed']=ok;_a11out.write_text(json.dumps({k:v for k,v in _a11.items() if k not in ('handle','source_listener','destination_listener','destination','started')},indent=2),encoding='utf-8');unreal.unregister_slate_post_tick_callback(_a11['handle']);globals()['_a24_job_result']=ok
def _a11tick(dt):
 try:
  assert time.monotonic()-_a11['started']<150,'A11 PIE timeout';_a11['frames']+=1;world=_a11ed.get_game_world()
  if _a11['phase']=='start':assert world is None;_a11lev.editor_request_begin_play();_a11['phase']='run';_a11['frames']=0;return
  if _a11['phase']=='run':
   if world is None or _a11['frames']<40:return
   pc=unreal.GameplayStatics.get_player_controller(world,0);ps=pc.get_editor_property('player_state');source=ps.get_component_by_class(_a11bp.generated_class());assert source and source.call_method('IsInitialized')
   dest=unreal.new_object(_a11bp.generated_class(),outer=ps);dest.call_method('InitializeInventory',(unreal.GameplayStatics.get_game_instance(world),4,10.));assert dest.call_method('IsInitialized');_a11['destination']=dest
   request=read(read(snapshot(source),'Slots')[0],'ItemStack');write(request,'ItemId','item.wood');write(request,'Quantity',10);assert result(source.call_method('TryAddExact',(request,)))==(True,1,10,1);guid=read(items(source)[0],'StackId')
   sx=unreal.new_object(_a11listener.generated_class());dx=unreal.new_object(_a11listener.generated_class());_a11['source_listener']=sx;_a11['destination_listener']=dx
   for listener,own,other in [(sx,source,dest),(dx,dest,source)]:listener.call_method('BindInventory',(own,));listener.set_editor_property('Other',other)
   raw=source.call_method('TryTransferExact',(dest,guid,3,1,0));assert result(raw[0])==(True,1,3,2) and raw[1]==1
   assert [read(v,'Quantity') for v in items(source)]==[7] and [read(v,'Quantity') for v in items(dest)]==[3]
   assert read(items(source)[0],'StackId').export_text()==guid.export_text() and read(items(dest)[0],'StackId').export_text()!=guid.export_text()
   assert sx.get_editor_property('OtherObserved').export_text()==snapshot(dest).export_text() and dx.get_editor_property('OtherObserved').export_text()==snapshot(source).export_text()
   before=[snapshot(o).export_text() for o in [source,dest]];raw=source.call_method('TryTransferExact',(dest,guid,1,1,0));assert result(raw[0])==(False,15,0,2) and raw[1]==1 and before==[snapshot(o).export_text() for o in [source,dest]]
   assert sx.get_editor_property('EventCount')==dx.get_editor_property('EventCount')==1 and list(sx.get_editor_property('LastChanged'))==list(dx.get_editor_property('LastChanged'))==[0]
   assert not source.get_editor_property('MutationInProgress') and not dest.get_editor_property('MutationInProgress')
   _a11['runs'].append({'passed':True,'source':7,'destination':3,'source_revision':2,'destination_revision':1,'source_events':1,'destination_events':1,'stale_rejected':True});_a11lev.editor_request_end_play();_a11['phase']='end';return
  if _a11['phase']=='end' and world is None:
   if len(_a11['runs'])==3:_a11finish(True)
   else:_a11['phase']='start'
 except Exception:
  _a11['error']=traceback.format_exc()
  if _a11ed.get_game_world():_a11lev.editor_request_end_play()
  _a11finish(False)
assert _a11lev.load_level('/Game/Survival/Maps/LV_SystemsTest');_a11['handle']=unreal.register_slate_post_tick_callback(_a11tick)
