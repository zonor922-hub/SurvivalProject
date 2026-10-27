"""Three fresh PIE worlds, commands on the actual PlayerState component; no saves."""
import unreal,json,pathlib,time,traceback,sys
from a09_verify import read,write,snapshot,result
from inventory_event_fixture import listener_class
_p={'phase':'start','frames':0,'runs':[],'started':time.monotonic()}
_lev=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem);_ed=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
_ibp=unreal.load_asset('/Game/Survival/Inventory/BPC_Inventory');_listener_bp=listener_class(_ibp)
_out=pathlib.Path(__file__).with_name('a09_pie.json')
def _finish(ok):
    _p['passed']=ok;_out.write_text(json.dumps({k:v for k,v in _p.items() if k not in ('handle','started','receiver')},indent=2,default=str),encoding='utf-8')
    unreal.unregister_slate_post_tick_callback(_p['handle']);globals()['_a24_job_result']=ok
def _tick(dt):
    try:
        assert time.monotonic()-_p['started']<120,'PIE timeout';_p['frames']+=1;w=_ed.get_game_world()
        if _p['phase']=='start':
            assert w is None;_lev.editor_request_begin_play();_p['phase']='run';_p['frames']=0;return
        if _p['phase']=='run':
            if w is None or _p['frames']<40:return
            gi=unreal.GameplayStatics.get_game_instance(w);pc=unreal.GameplayStatics.get_player_controller(w,0);ps=pc.get_editor_property('player_state');o=ps.get_component_by_class(_ibp.generated_class())
            assert gi.get_editor_property('CatalogReady') and pc.get_editor_property('BootstrapReady') and ps.get_editor_property('BootstrapReady')
            assert read(snapshot(o),'Revision')==0 and o.call_method('GetCurrentWeight')==(0.,True)
            receiver=unreal.new_object(_listener_bp.generated_class());_p['receiver']=receiver;receiver.call_method('BindInventory',(o,))
            s=read(read(snapshot(o),'Slots')[0],'ItemStack');write(s,'ItemId','item.wood');write(s,'Quantity',20)
            assert result(o.call_method('TryAddExact',(s,)))==(True,1,20,1)
            assert result(o.call_method('TryRemoveExact',('item.wood',2)))==(True,1,2,2)
            before=snapshot(o).export_text();assert not result(o.call_method('TryRemoveExact',('item.wood',0)))[0];assert before==snapshot(o).export_text()
            o.call_method('InitializeInventory',(gi,1,0.));assert before==snapshot(o).export_text() and o.call_method('GetCurrentWeight')==(9.,True)
            assert receiver.get_editor_property('EventCount')==2 and receiver.get_editor_property('LastRevision')==2
            assert list(receiver.get_editor_property('LastChanged'))==[0]
            assert 'ABP_Survival' in unreal.GameplayStatics.get_player_pawn(w,0).get_component_by_class(unreal.SkeletalMeshComponent).get_anim_instance().get_class().get_path_name()
            _p['runs'].append({'passed':True,'revision':2,'weight':9.,'events':2,'catalog_entries':len(gi.get_editor_property('ItemDefinitions'))});_lev.editor_request_end_play();_p['phase']='end';return
        if _p['phase']=='end' and w is None:
            if len(_p['runs'])==3:_finish(True)
            else:_p['phase']='start'
    except Exception:
        _p['error']=traceback.format_exc()
        if _ed.get_game_world():_lev.editor_request_end_play()
        _finish(False)
assert _lev.load_level('/Game/Survival/Maps/LV_SystemsTest')
_p['handle']=unreal.register_slate_post_tick_callback(_tick)
