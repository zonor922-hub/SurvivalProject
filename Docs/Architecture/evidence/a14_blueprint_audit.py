import unreal,json,traceback,pathlib
out={'engine':unreal.SystemLibrary.get_engine_version(),'assets':{},'graphs':{}}
B=unreal.BlueprintEditorLibrary; P=unreal.BlueprintGraphPinLibrary
try:
 for path in ['/Game/Survival/Core/BP_SurvivalPlayerController','/Game/Survival/Input/Actions/IA_Interact','/Game/Survival/Input/Actions/IA_Inventory','/Game/Survival/Input/IMC_Survival','/Game/Survival/Input/ESurvivalInputMode']:
  a=unreal.load_asset(path); out['assets'][path]={'loaded':bool(a),'class':a.get_class().get_name() if a else None}
  if isinstance(a,unreal.Blueprint):
   out['assets'][path]['compiled']=B.compile_blueprint(a);out['assets'][path]['status']=str(a.get_editor_property('status'))
   for g in B.list_graph_names(a):
    ed=unreal.BlueprintGraphEditor.get_graph_editor_by_name(a,str(g)); nodes=[]
    for n in ed.list_all_nodes():
     pins=[]
     for p in B.list_all_pins(n):
      pins.append({'name':str(P.get_pin_name(p)),'direction':str(P.get_pin_direction(p)),'value':str(P.get_pin_value(p)),'links':[P.get_owning_node(q).get_name()+':'+str(P.get_pin_name(q)) for q in P.list_connected_pins(p)]})
     nodes.append({'name':n.get_name(),'class':n.get_class().get_name(),'title':str(B.get_node_title(n)),'pins':pins})
    out['graphs'][str(g)]=nodes
except:out['error']=traceback.format_exc()
with open(str(pathlib.Path(__file__).resolve().parents[3]/'Saved/a14_audit.json'),'w',encoding='utf-8') as f:json.dump(out,f,ensure_ascii=False,indent=2,default=str)
