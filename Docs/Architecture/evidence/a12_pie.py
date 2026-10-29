"""Run from Python console during a user-started fresh PIE session; never starts PIE."""
import sys, pathlib, json, traceback, datetime, unreal
source = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(source))
from a12_suite import suite
scenario = int(globals()['SCENARIO'])
report = {'scenario': scenario, 'mode': 'user-started PIE', 'tests': [], 'passed': False,
          'engine_version': unreal.SystemLibrary.get_engine_version()}
try:
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    assert world, 'Start a fresh PIE session first'
    assert scenario in (1, 2, 3)
    bp = unreal.load_asset('/Game/Survival/Inventory/BPC_Inventory')
    pc = unreal.GameplayStatics.get_player_controller(world, 0)
    ps = pc.get_editor_property('player_state')
    inv = ps.get_component_by_class(bp.generated_class())
    assert inv and inv.call_method('IsInitialized')
    suite(unreal.GameplayStatics.get_game_instance(world), bp, scenario, report['tests'], primary=inv)
    report['passed'] = True
except Exception:
    report['error'] = traceback.format_exc()
finally:
    output = pathlib.Path(unreal.Paths.project_saved_dir())/'Verification'/'A12'/'Manual'
    output.mkdir(parents=True, exist_ok=True)
    path = output/(datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ') + '_scenario' + str(scenario) + '.json')
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    unreal.log('A12 scenario %s: %s; evidence: %s' % (scenario, 'PASS' if report['passed'] else 'FAIL', path))
