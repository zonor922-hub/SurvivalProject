"""Read-only A07 editor checks; restore earlier task results after regression tests."""
import json
import pathlib
import traceback
import unreal

folder = pathlib.Path(__file__).resolve().parent
result = {'engine_version': unreal.SystemLibrary.get_engine_version(), 'project_directory': unreal.Paths.project_dir(), 'regression': {}, 'compile': {}, 'visuals': []}
try:
    for task in ('a05', 'a06'):
        script = folder / (task + '_verify.py')
        output = folder / (task + '_verification.json')
        original = output.read_bytes()
        try:
            exec(compile(script.read_text(encoding='utf-8'), str(script), 'exec'), {'__file__': str(script)})
            check = json.loads(output.read_text(encoding='utf-8'))
            result['regression'][task] = check
            assert check['passed'], task
        finally:
            output.write_bytes(original)
    registry = unreal.AssetRegistryHelpers.get_asset_registry()
    registry.search_all_assets(True)
    for asset in registry.get_assets_by_path('/Game/Survival', recursive=True):
        obj = asset.get_asset()
        if isinstance(obj, unreal.Blueprint):
            assert unreal.BlueprintEditorLibrary.compile_blueprint(obj), obj.get_path_name()
            status = str(obj.get_editor_property('status'))
            result['compile'][obj.get_path_name()] = status
            assert 'BS_UP_TO_DATE' in status, obj.get_path_name()
    for name in ('Wood', 'Stone', 'Berry', 'Plank'):
        definition = unreal.load_asset('/Game/Survival/Items/Definitions/DA_Item_' + name)
        for field, expected in (('WorldMesh', unreal.StaticMesh), ('Icon', unreal.Texture2D)):
            obj = definition.get_editor_property(field)
            assert isinstance(obj, expected), (name, field, obj)
            result['visuals'].append({'item_id': str(definition.get_editor_property('ItemId')), 'field': field, 'path': obj.get_path_name()})
    level = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    assert level.load_level('/Game/Survival/Maps/LV_SystemsTest')
    probe = unreal.load_asset('/Game/Survival/Tests/BP_CatalogCookProbe')
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
    result['probe_count'] = sum(a.get_class() == probe.generated_class() for a in actors)
    assert result['probe_count'] == 1
    result['passed'] = True
except Exception:
    result['passed'] = False
    result['error'] = traceback.format_exc()
(folder / 'a07_editor_verification.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
assert result['passed'], result.get('error', 'A07 failed')
