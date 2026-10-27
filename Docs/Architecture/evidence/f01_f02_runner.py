"""Editor process for run_f01_f02.ps1. Results are written outside source evidence."""
import unreal,pathlib,json,sys,os,time,traceback
context=json.loads(pathlib.Path(os.environ['SURVIVAL_TEST_CONTEXT']).read_text(encoding='utf-8-sig'))
source=pathlib.Path(context['source']);output=pathlib.Path(context['output']);sys.path.insert(0,str(source))
summary={'context':context,'include_a10':context.get('include_a10',True),'engine_version':unreal.SystemLibrary.get_engine_version(),'contracts':[],'integration':[],'compile':{},'diagnostics':[],'passed':False}
def save(): (output/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
def execute(name,namespace=None):
    namespace=namespace if namespace is not None else {}
    namespace.update({'__name__':'__main__','__file__':str(output/name)})
    exec(compile((source/name).read_text(encoding='utf-8-sig'),str(source/name),'exec'),namespace)
def finish(ok):
    summary['passed']=ok;save()
    if 'handle' in state:unreal.unregister_slate_post_tick_callback(state['handle'])
    unreal.EditorPythonScripting.set_keep_python_script_alive(False)
state={'index':0,'active':False,'started':time.monotonic()}
try:
    contracts=[('a05_verify.py','a05_verification.json'),('a06_verify.py','a06_verification.json'),('a08_access_verify.py','a08_access_verification.json'),('a08_verify.py','a08_verification.json'),('a09_access_verify.py','a09_access_verification.json'),('a09_verify.py','a09_verification.json'),('a09_model_verify.py','a09_model_verification.json'),('f02_verify.py','f02_verification.json')]
    if summary['include_a10']:contracts += [('a10_access_verify.py','a10_access_verification.json'),('a10_verify.py','a10_verification.json')]
    for script,result_name in contracts:
        error=None
        try:execute(script)
        except Exception:error=traceback.format_exc()
        result=json.loads((output/result_name).read_text(encoding='utf-8')) if (output/result_name).exists() else {'passed':False,'tests':[]}
        summary['contracts'].append({'script':script,'result':result_name,'passed':result.get('passed',False) and not error,'tests':len(result.get('tests',[])),'model_operations':result.get('random_cases',0),'error':error})
        save()
    registry=unreal.AssetRegistryHelpers.get_asset_registry();registry.search_all_assets(True)
    compile_assets=list(registry.get_assets_by_path('/Game/Survival',recursive=True))
    if summary['include_a10']:compile_assets+=list(registry.get_assets_by_package_name('/Game/__A09Test/Listener'))
    for asset in compile_assets:
        bp=asset.get_asset()
        if not isinstance(bp,unreal.Blueprint):continue
        ok=unreal.BlueprintEditorLibrary.compile_blueprint(bp);status=bp.get_editor_property('status');summary['compile'][bp.get_path_name()]={'success':ok,'status':str(status)}
        assert ok and status in (unreal.BlueprintStatus.BS_UP_TO_DATE,unreal.BlueprintStatus.BS_UP_TO_DATE_WITH_WARNINGS),bp.get_path_name()
        for name in unreal.BlueprintEditorLibrary.list_graph_names(bp):
            ed=unreal.BlueprintGraphEditor.get_graph_editor_by_name(bp,str(name))
            if ed:
                for n in ed.list_all_nodes():
                    try:message=n.get_editor_property('error_msg')
                    except Exception:message=''
                    if message:summary['diagnostics'].append({'asset':bp.get_path_name(),'graph':str(name),'message':message})
    inv=unreal.load_asset('/Game/Survival/Inventory/BPC_Inventory')
    assert all(unreal.BlueprintEditorLibrary.find_graph(inv,name) is None for name in ('A09TestSetGuard','A09TestSetSlots','A10SeedSlots','A10SeedGuard','A10SeedRevision','A10SeedWeightLimit')),'Fixture functions left behind'
    jobs=['a09_pie.py']
    if summary['include_a10']:jobs.append('a10_pie.py')
    if not context['skip_swimming']:
        levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
        assert levels.load_level('/Game/Content/Survival/Maps/LV_Survival_Nature')
        volumes=[a for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors() if isinstance(a,unreal.PhysicsVolume) and a.get_actor_label().startswith('LakeSwimVolume')]
        assert len(volumes)==257
        for v in volumes:
            center,extent=v.get_actor_bounds(False)
            assert abs(center.z+extent.z)<.1 and abs(center.z-extent.z+450)<.1 and v.get_editor_property('water_volume') and v.get_editor_property('priority')==10
        summary['water_volumes']=257
        jobs+=['a24_move_verify.py','a24_physics_after.py','a24_shore_verify.py']
    save();unreal.EditorPythonScripting.set_keep_python_script_alive(True)
    def tick(dt):
        try:
            assert time.monotonic()-state['started']<600,'Integration suite timeout'
            if state['active']:
                if '_a24_job_result' not in globals():return
                ok=globals().pop('_a24_job_result');summary['integration'].append({'script':jobs[state['index']],'passed':ok});save()
                assert ok,jobs[state['index']]
                state['index']+=1;state['active']=False;return
            if unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world():return
            if state['index']==len(jobs):
                assert not context.get('inject_failure'), 'Intentional runner failure propagation test'
                finish(all(x['passed'] for x in summary['contracts']));return
            name=jobs[state['index']]
            if name not in ('a09_pie.py','a10_pie.py'):
                levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
                assert levels.load_level('/Game/Survival/Maps/LV_SystemsTest' if name=='a24_move_verify.py' else '/Game/Content/Survival/Maps/LV_Survival_Nature')
            state['active']=True;execute(name,globals())
        except Exception:
            summary['error']=traceback.format_exc();unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).editor_request_end_play();finish(False)
    state['handle']=unreal.register_slate_post_tick_callback(tick)
except Exception:
    summary['error']=traceback.format_exc();save()
    raise
