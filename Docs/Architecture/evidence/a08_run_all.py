import unreal,pathlib,json
folder=pathlib.Path(__file__).resolve().parent
for name,result in (('a08_access_verify.py','a08_access_verification.json'),('a08_verify.py','a08_verification.json')):
 script=folder/name;exec(compile(script.read_text(encoding='utf-8'),str(script),'exec'),{'__file__':str(script)})
 assert json.loads((folder/result).read_text(encoding='utf-8'))['passed'],result
registry=unreal.AssetRegistryHelpers.get_asset_registry();registry.search_all_assets(True)
compiled={}
for asset in registry.get_assets_by_path('/Game/Survival',recursive=True):
 bp=asset.get_asset()
 if isinstance(bp,unreal.Blueprint):
  assert unreal.BlueprintEditorLibrary.compile_blueprint(bp),bp.get_path_name()
  compiled[bp.get_path_name()]=str(bp.get_editor_property('status'));assert 'BS_UP_TO_DATE' in compiled[bp.get_path_name()]
(folder/'a08_compile.json').write_text(json.dumps(compiled,indent=2),encoding='utf-8')
unreal.EditorPythonScripting.set_keep_python_script_alive(True)
script=folder/'a08_pie.py';globals()['__file__']=str(script);exec(compile(script.read_text(encoding='utf-8'),str(script),'exec'),globals())
