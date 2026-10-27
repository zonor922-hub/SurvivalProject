"""Three real PIE starts and A10 commands on the actual PlayerState inventory."""
import unreal,pathlib,json,time,traceback
from a09_verify import read,write,snapshot,result,items
from a10_event_fixture import listener_class
_a10={'phase':'start','frames':0,'runs':[],'started':time.monotonic()}
_a10ed=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem);_a10lev=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
_a10bp=unreal.load_asset('/Game/Survival/Inventory/BPC_Inventory');_a10receiver=listener_class(_a10bp)
_a10out=pathlib.Path(__file__).with_name('a10_pie.json')
def _a10finish(ok):
    _a10['passed']=ok;_a10out.write_text(json.dumps({k:v for k,v in _a10.items() if k not in ('handle','receiver','started')},indent=2),encoding='utf-8');unreal.unregister_slate_post_tick_callback(_a10['handle']);globals()['_a24_job_result']=ok
def _a10tick(dt):
    try:
        assert time.monotonic()-_a10['started']<150,'A10 PIE timeout';_a10['frames']+=1;w=_a10ed.get_game_world()
        if _a10['phase']=='start':assert w is None;_a10lev.editor_request_begin_play();_a10['phase']='run';_a10['frames']=0;return
        if _a10['phase']=='run':
            if w is None or _a10['frames']<40:return
            pc=unreal.GameplayStatics.get_player_controller(w,0);o=pc.get_editor_property('player_state').get_component_by_class(_a10bp.generated_class());assert o and o.call_method('IsInitialized')
            s=read(read(snapshot(o),'Slots')[0],'ItemStack');write(s,'ItemId','item.wood');write(s,'Quantity',10);assert result(o.call_method('TryAddExact',(s,)))==(True,1,10,1)
            original=read(items(o)[0],'StackId');receiver=unreal.new_object(_a10receiver.generated_class());_a10['receiver']=receiver;receiver.call_method('BindInventory',(o,))
            assert result(o.call_method('TrySplit',(original,4,1)))==(True,1,4,2);split_items=items(o);assert [read(s,'Quantity') for s in split_items]==[6,4]
            created=read(split_items[1],'StackId');assert created.export_text()!=original.export_text() and unreal.GuidLibrary.is_valid_guid(created)
            assert receiver.get_editor_property('EventCount')==1 and list(receiver.get_editor_property('LastChanged'))==[0,1]
            assert result(o.call_method('TryMerge',(created,original)))==(True,1,4,3);assert read(items(o)[0],'StackId').export_text()==original.export_text() and len(items(o))==1
            before=snapshot(o).export_text();r=result(o.call_method('TrySplit',(original,0,1)));assert r==(False,6,0,3) and snapshot(o).export_text()==before
            assert receiver.get_editor_property('EventCount')==2 and list(receiver.get_editor_property('LastChanged'))==[1,0] and receiver.get_editor_property('ObservedRevision')==3
            assert o.call_method('GetCurrentWeight')==(5.,True) and not o.get_editor_property('MutationInProgress') and not o.is_component_tick_enabled()
            _a10['runs'].append({'passed':True,'split':[6,4],'merged':10,'weight':5.,'revision':3,'events':2});_a10lev.editor_request_end_play();_a10['phase']='end';return
        if _a10['phase']=='end' and w is None:
            if len(_a10['runs'])==3:_a10finish(True)
            else:_a10['phase']='start'
    except Exception:
        _a10['error']=traceback.format_exc()
        if _a10ed.get_game_world():_a10lev.editor_request_end_play()
        _a10finish(False)
assert _a10lev.load_level('/Game/Survival/Maps/LV_SystemsTest')
_a10['handle']=unreal.register_slate_post_tick_callback(_a10tick)
