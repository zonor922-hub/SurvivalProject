"""A12 process entry; each scenario repeated with identical inputs three times."""
import os, sys, pathlib, json, traceback, unreal
context = json.loads(pathlib.Path(os.environ['SURVIVAL_TEST_CONTEXT']).read_text(encoding='utf-8-sig'))
source = pathlib.Path(context['source']); output = pathlib.Path(context['output'])
sys.path.insert(0, str(source))
from a12_suite import suite
summary = {'context': context, 'engine_version': unreal.SystemLibrary.get_engine_version(), 'tests': [], 'runs': [], 'passed': False}
try:
    assert summary['engine_version'].startswith('5.8.4-'), summary['engine_version']
    bp = unreal.load_asset('/Game/Survival/Inventory/BPC_Inventory')
    assert unreal.BlueprintEditorLibrary.compile_blueprint(bp), 'Inventory compilation'
    summary['compile_status'] = str(bp.get_editor_property('status'))
    gi = unreal.new_object(unreal.load_asset('/Game/Survival/Core/BP_SurvivalGameInstance').generated_class())
    gi.call_method('InitializeCatalog')
    assert gi.get_editor_property('CatalogReady')
    for repeat in range(1, 4):
        for scenario in (1, 2, 3):
            start = len(summary['tests'])
            suite(gi, bp, scenario, summary['tests'])
            summary['runs'].append({'repeat': repeat, 'scenario': scenario, 'assertions': len(summary['tests']) - start, 'passed': True})
    assert not context.get('inject_failure'), 'Intentional runner failure propagation test'
    summary['passed'] = True
except Exception:
    summary['error'] = traceback.format_exc()
finally:
    summary['pass_assertions'] = sum(t['passed'] for t in summary['tests'])
    summary['fail_assertions'] = sum(not t['passed'] for t in summary['tests'])
    (output/'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
