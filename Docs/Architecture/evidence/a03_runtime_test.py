"""A03 functional verification in PIE only. No asset, map or editor settings writes."""
import unreal,json,pathlib,time,traceback,math
a03_out=pathlib.Path(r'<LOCAL_WORKSPACE>\Architecture\evidence')
a03_test={'started':time.monotonic(),'phase':'travel','frame':0,'report':{'checks':{},'snapshots':[],'errors':[]},'mapping_events':[]}
a03_gm='/Game/Survival/Core/BP_SurvivalGameMode.BP_SurvivalGameMode_C'
a03_map='/Game/Content/Survival/Maps/LV_Survival_Nature'
def a03_write_progress():
    (a03_out/'a03_runtime_progress.json').write_text(json.dumps({'phase':a03_test['phase'],'frame':a03_test['frame'],'errors':a03_test['report']['errors']},indent=2),encoding='utf-8')
def a03_snapshot():
    world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    pc=unreal.GameplayStatics.get_player_controller(world,0)
    pawn=unreal.GameplayStatics.get_player_pawn(world,0)
    gi=unreal.GameplayStatics.get_game_instance(world)
    gm=unreal.GameplayStatics.get_game_mode(world)
    ps=pc.get_editor_property('player_state')
    objs={'game_instance':gi,'game_mode':gm,'controller':pc,'player_state':ps,'character':pawn}
    snapshot={'world':world.get_path_name(),'classes':{},'initialize_count':{},'ready':{},'actor_counts':{}}
    for key,obj in objs.items():
        snapshot['classes'][key]=obj.get_class().get_path_name()
        snapshot['initialize_count'][key]=obj.get_editor_property('InitializeCount')
        snapshot['ready'][key]=obj.get_editor_property('BootstrapReady')
        if key!='game_instance':snapshot['actor_counts'][key]=len(unreal.GameplayStatics.get_all_actors_of_class(world,obj.get_class()))
    snapshot['possession_generation']=pc.get_editor_property('PossessionGeneration')
    snapshot['enhanced_input_components']=len(pawn.get_components_by_class(unreal.EnhancedInputComponent))
    snapshot['bound_pawn_correct']=pc.get_editor_property('BoundPawn')==pawn
    snapshot['bound_player_state_correct']=pc.get_editor_property('BoundPlayerState')==ps
    snapshot['bound_game_instance_correct']=pc.get_editor_property('BoundGameInstance')==gi
    return world,pc,pawn,objs,snapshot
def a03_inject(action,vector):
    a03_test['subsystem'].inject_input_vector_for_action(a03_test['actions'][action],unreal.Vector(*vector),[],[])
def a03_next(phase):
    a03_test['phase']=phase;a03_test['frame']=0;a03_write_progress()
def a03_finish(success):
    a03_test['report']['success']=success
    a03_test['report']['elapsed_seconds']=time.monotonic()-a03_test['started']
    a03_test['report']['mapping_context_additions_during_repossession']=a03_test['mapping_events']
    (a03_out/'a03_runtime_result.json').write_text(json.dumps(a03_test['report'],ensure_ascii=False,indent=2),encoding='utf-8')
    if a03_test.get('subsystem'):
        a03_test['subsystem'].on_mapping_context_added.remove_callable(a03_context_added)
    unreal.unregister_slate_post_tick_callback(a03_test['handle'])
    unreal.log('A03_RUNTIME_RESULT '+json.dumps(a03_test['report'],ensure_ascii=True))
def a03_context_added(ctx):a03_test['mapping_events'].append(ctx.get_path_name())
def a03_tick(delta):
    try:
        if time.monotonic()-a03_test['started']>180:raise RuntimeError('A03 runtime verification timeout')
        phase=a03_test['phase'];a03_test['frame']+=1;frame=a03_test['frame']
        world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
        if world is None:raise RuntimeError('PIE is not running')
        if phase=='travel':
            a03_next('await_custom_world')
            unreal.GameplayStatics.open_level(world,a03_map,True,'game='+a03_gm)
            return
        gm=unreal.GameplayStatics.get_game_mode(world)
        if gm is None or gm.get_class().get_path_name()!=a03_gm:return
        if phase=='await_custom_world':
            if frame<15:return
            world,pc,pawn,objs,s=a03_snapshot()
            assert all(v==1 for v in s['initialize_count'].values()),s
            assert all(s['ready'].values()),s
            assert all(v==1 for v in s['actor_counts'].values()),s
            assert all(s[k] for k in ('bound_pawn_correct','bound_player_state_correct','bound_game_instance_correct')),s
            a03_test['report']['snapshots'].append(s)
            a03_test['pc']=pc;a03_test['pawn']=pawn;a03_test['objects']=objs
            candidates=[o for o in unreal.ObjectIterator(unreal.EnhancedInputLocalPlayerSubsystem) if isinstance(o.get_outer(),unreal.LocalPlayer)]
            assert len(candidates)==1,[o.get_path_name() for o in candidates]
            subsystem=candidates[0]
            assert subsystem is not None
            a03_test['subsystem']=subsystem
            a03_test['actions']={name:unreal.load_asset('/Game/Input/Actions/'+name) for name in ('IA_Move','IA_MouseLook','IA_Jump')}
            assert subsystem.has_mapping_context(unreal.load_asset('/Game/Input/IMC_Default')) is not None
            assert subsystem.has_mapping_context(unreal.load_asset('/Game/Input/IMC_MouseLook')) is not None
            subsystem.on_mapping_context_added.add_callable(a03_context_added)
            a03_test['report']['checks']['unique_classes_and_ready']=True
            a03_test['report']['checks']['mapping_contexts_present']=True
            for key,obj in objs.items():
                if key!='controller':
                    obj.call_method('InitializeBootstrap');obj.call_method('InitializeBootstrap')
            pc.call_method('TryInitialize');pc.call_method('TryInitialize')
            _,_,_,_,again=a03_snapshot()
            assert all(v==1 for v in again['initialize_count'].values()),again
            assert again['possession_generation']==s['possession_generation'],again
            a03_test['report']['checks']['idempotent_initialize']=True
            a03_test['yaw_before']=pc.get_control_rotation().yaw
            a03_inject('IA_MouseLook',(1,0,0));a03_next('measure_look_before');return
        pc=a03_test['pc'];pawn=a03_test['pawn']
        if phase=='measure_look_before':
            if frame<4:return
            angle=((pc.get_control_rotation().yaw-a03_test['yaw_before']+180)%360)-180
            assert abs(angle)>0.001,angle
            a03_test['report']['look_delta_before']=angle
            a03_test['walk_start']=pawn.get_actor_location()
            a03_test['walk_peak']=0.0
            a03_next('walk');return
        if phase=='walk':
            a03_inject('IA_Move',(0,1,0))
            a03_test['walk_peak']=max(a03_test['walk_peak'],pawn.get_velocity().length())
            if frame<20:return
            displacement=(pawn.get_actor_location()-a03_test['walk_start']).length()
            assert displacement>1 and a03_test['walk_peak']>1,(displacement,a03_test['walk_peak'])
            a03_test['report']['walk_distance_cm']=displacement
            a03_test['report']['walk_peak_speed']=a03_test['walk_peak']
            a03_test['report']['checks']['enhanced_input_movement']=True
            a03_next('settle');return
        if phase=='settle':
            if frame<15:return
            a03_test['jump_start_z']=pawn.get_actor_location().z;a03_test['jump_peak']=0.0
            a03_inject('IA_Jump',(1,0,0));a03_next('jump');return
        if phase=='jump':
            a03_test['jump_peak']=max(a03_test['jump_peak'],pawn.get_actor_location().z-a03_test['jump_start_z'])
            if frame<35:return
            assert a03_test['jump_peak']>10,a03_test['jump_peak']
            a03_test['report']['jump_height_cm']=a03_test['jump_peak']
            a03_test['report']['checks']['enhanced_input_jump']=True
            a03_next('repossession');return
        if phase=='repossession':
            pc.un_possess()
            assert not pc.get_editor_property('BootstrapReady')
            pc.call_method('TryInitialize')
            assert not pc.get_editor_property('BootstrapReady')
            assert pc.get_editor_property('BoundPawn') is None
            pc.possess(pawn)
            assert pc.get_editor_property('BootstrapReady')
            if frame<3:return
            a03_test['report']['checks']['unpossessed_negative_case']=True
            a03_next('after_repossession');return
        if phase=='after_repossession':
            if frame<15:return
            _,_,_,_,s=a03_snapshot()
            assert all(v==1 for v in s['initialize_count'].values()),s
            assert all(v==1 for v in s['actor_counts'].values()),s
            assert s['enhanced_input_components']==1,s
            assert s['possession_generation']==4,s
            assert not a03_test['mapping_events'],a03_test['mapping_events']
            a03_test['report']['snapshots'].append(s)
            a03_test['report']['checks']['three_repossessions_no_extra_contexts']=True
            a03_test['yaw_before']=pc.get_control_rotation().yaw
            a03_inject('IA_MouseLook',(1,0,0));a03_next('measure_look_after');return
        if phase=='measure_look_after':
            if frame<4:return
            angle=((pc.get_control_rotation().yaw-a03_test['yaw_before']+180)%360)-180
            before=a03_test['report']['look_delta_before']
            assert abs(angle-before)<0.05,(before,angle)
            a03_test['report']['look_delta_after']=angle
            a03_test['report']['checks']['same_single_input_response_after_repossession']=True
            a03_test['report']['camera_components']=len(pawn.get_components_by_class(unreal.CameraComponent))
            a03_test['report']['spring_arms']=len(pawn.get_components_by_class(unreal.SpringArmComponent))
            assert a03_test['report']['camera_components']==1 and a03_test['report']['spring_arms']==1
            a03_test['report']['checks']['camera_inherited']=True
            a03_finish(True)
    except Exception:
        a03_test['report']['errors'].append(traceback.format_exc());a03_finish(False)
a03_test['handle']=unreal.register_slate_post_tick_callback(a03_tick)
a03_write_progress()
