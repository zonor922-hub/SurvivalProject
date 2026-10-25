"""Three independent PIE sessions; fixture reset and CSV timing baseline."""
import unreal,json,pathlib,time,traceback
a4out=pathlib.Path(r'<LOCAL_WORKSPACE>/Architecture/evidence')
a4levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
a4editor=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
a4={'phase':'start','frame':0,'runs':[],'errors':[],'started':time.monotonic()}
def a4phase(name):a4['phase']=name;a4['frame']=0
def a4finish(ok):
    a4['success']=ok
    (a4out/'a04_runtime_result.json').write_text(json.dumps({k:v for k,v in a4.items() if k not in ('handle','started')},indent=2),encoding='utf-8')
    unreal.unregister_slate_post_tick_callback(a4['handle'])
    unreal.log('A04_RUNTIME '+str(ok))
def a4tick(dt):
    try:
        assert time.monotonic()-a4['started']<240,'Timeout'
        a4['frame']+=1;f=a4['frame'];phase=a4['phase']
        w=a4editor.get_game_world()
        if phase=='start':
            assert w is None
            assert 'LV_SystemsTest' in a4editor.get_editor_world().get_path_name()
            a4levels.editor_request_begin_play();a4phase('warmup');return
        if phase=='warmup':
            if w is None or f<120:return
            pc=unreal.GameplayStatics.get_player_controller(w,0);pawn=unreal.GameplayStatics.get_player_pawn(w,0)
            gi=unreal.GameplayStatics.get_game_instance(w);gm=unreal.GameplayStatics.get_game_mode(w);ps=pc.get_editor_property('player_state')
            objs={'gi':gi,'gm':gm,'pc':pc,'ps':ps,'pawn':pawn}
            classes={k:o.get_class().get_path_name() for k,o in objs.items()}
            assert all('BP_Survival' in c for c in classes.values()),classes
            assert all(o.get_editor_property('InitializeCount')==1 and o.get_editor_property('BootstrapReady') for o in objs.values())
            fixtures=unreal.GameplayStatics.get_all_actors_of_class(w,unreal.load_class(None,'/Game/Survival/Tests/BP_SystemsTestFixture.BP_SystemsTestFixture_C'))
            assert len(fixtures)==1
            fixture=fixtures[0]
            initial={'value':fixture.get_editor_property('TestValue'),'flag':fixture.get_editor_property('TestFlag')}
            assert initial=={'value':0,'flag':False}
            fixture.set_editor_property('TestValue',73);fixture.set_editor_property('TestFlag',True)
            fixture.call_method('ResetTestData');fixture.call_method('ResetTestData')
            assert fixture.get_editor_property('TestValue')==0 and not fixture.get_editor_property('TestFlag')
            loc=pawn.get_actor_location();rot=pc.get_control_rotation()
            record={'run':len(a4['runs'])+1,'classes':classes,'location_cm':[round(loc.x,2),round(loc.y,2),round(loc.z,2)],'control_rotation':[round(rot.pitch,2),round(rot.yaw,2),round(rot.roll,2)],'fixture_initial':initial,'reset_idempotent':True,'initialize_counts':{k:o.get_editor_property('InitializeCount') for k,o in objs.items()},'pawn_count':len(unreal.GameplayStatics.get_all_actors_of_class(w,pawn.get_class()))}
            assert record['pawn_count']==1
            a4['runs'].append(record)
            if len(a4['runs'])<3:
                a4levels.editor_request_end_play();a4phase('wait_end');return
            assert all({k:v for k,v in r.items() if k!='run'}=={k:v for k,v in a4['runs'][0].items() if k!='run'} for r in a4['runs'])
            a4['three_identical_starts']=True
            cv=unreal.SystemLibrary
            a4['conditions']={'engine':cv.get_engine_version(),'viewport':list(pc.get_viewport_size()),'warmup_frames':120,'capture_frames':300,'camera':'ThirdPerson at unmodified PlayerStart; no input','cvars':{n:cv.get_console_variable_float_value(n) for n in ['r.VSync','t.MaxFPS','r.ScreenPercentage','sg.ViewDistanceQuality','sg.ShadowQuality','sg.GlobalIlluminationQuality','sg.ReflectionQuality','sg.PostProcessQuality','sg.TextureQuality','sg.EffectsQuality','sg.FoliageQuality','r.DynamicGlobalIlluminationMethod','r.ReflectionMethod']}}
            unreal.SystemLibrary.execute_console_command(w,'csvprofile frames=300')
            a4phase('profile');return
        if phase=='wait_end':
            if w is not None or f<10:return
            a4phase('start');return
        if phase=='profile':
            if f<330:return
            a4levels.editor_request_end_play();a4phase('final_end');return
        if phase=='final_end':
            if w is not None:return
            a4finish(True)
    except Exception:
        a4['errors'].append(traceback.format_exc())
        if a4editor.get_game_world() is not None:a4levels.editor_request_end_play()
        a4finish(False)
a4['handle']=unreal.register_slate_post_tick_callback(a4tick)
