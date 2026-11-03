import unreal,json,pathlib,traceback
root=pathlib.Path(unreal.Paths.project_dir())
out={'engine':unreal.SystemLibrary.get_engine_version(),'assets':{},'graphs':{}}
B=unreal.BlueprintEditorLibrary;P=unreal.BlueprintGraphPinLibrary
paths=['/Game/Survival/UI/Inventory/WBP_Inventory','/Game/Survival/UI/Inventory/WBP_InventorySlot','/Game/Survival/Core/BP_SurvivalPlayerController','/Game/Survival/Inventory/BPC_Inventory','/Game/Survival/UI/WBP_HUD','/Game/Survival/Input/IMC_Survival']
try:
 for path in paths:
  a=unreal.load_asset(path); entry={'loaded':bool(a)};out['assets'][path]=entry
  if not a:continue
  entry['class']=a.get_class().get_name()
  entry['dependencies']=[str(x) for x in unreal.AssetRegistryHelpers.get_asset_registry().get_dependencies(path,unreal.AssetRegistryDependencyOptions(include_soft_package_references=True,include_hard_package_references=True))]
  if path.endswith('IMC_Survival'):
   entry['mappings']=[{'action':str(m.action.get_path_name()),'key':str(m.key.export_text())} for m in a.get_editor_property('mappings')]
  if not isinstance(a,unreal.Blueprint):continue
  B.compile_blueprint(a);entry['status']=str(a.get_editor_property('status'))
  for g in B.list_graph_names(a):
   ed=unreal.BlueprintGraphEditor.get_graph_editor_by_name(a,str(g));nodes=[]
   for n in ed.list_all_nodes():
    pins=[]
    for p in B.list_all_pins(n):
     pins.append({'name':str(P.get_pin_name(p)),'direction':str(P.get_pin_direction(p)),'value':str(P.get_pin_value(p)),'links':[P.get_owning_node(q).get_name()+':'+str(P.get_pin_name(q)) for q in P.list_connected_pins(p)]})
    nodes.append({'name':n.get_name(),'title':str(B.get_node_title(n)),'pins':pins})
   out['graphs'][path+':'+str(g)]=nodes
except:out['error']=traceback.format_exc()
(root/'Saved/A17Audit/graphs.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
unreal.SystemLibrary.quit_editor()
