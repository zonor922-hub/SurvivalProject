import unreal,json,pathlib,traceback
out=pathlib.Path('D:/Project/SurvivalProject_A11/Saved/Verification/A11')
r={'engine':unreal.SystemLibrary.get_engine_version(),'project':unreal.Paths.project_dir(),'graphs':{}}
try:
 b=unreal.load_asset('/Game/Survival/Inventory/BPC_Inventory')
 B=unreal.BlueprintEditorLibrary; P=unreal.BlueprintGraphPinLibrary
 r['graph_names']=[str(x) for x in B.list_graph_names(b)]
 for name in ['SimulateAddExact','TryAddExact','ValidateSlots']:
  ed=unreal.BlueprintGraphEditor.get_graph_editor_by_name(b,name)
  rows=[]
  for n in ed.list_all_nodes():
   row={'name':n.get_name(),'class':n.get_class().get_name(),'title':str(B.get_node_title(n)),'pins':[]}
   for p in B.list_all_pins(n):
    item={'name':str(P.get_pin_name(p)),'direction':str(P.get_pin_direction(p))}
    for prop in ['get_pin_value','get_pin_default_value']:
     if hasattr(P,prop):
      try:item[prop]=str(getattr(P,prop)(p))
      except Exception:pass
    item['connections']=[{'node':P.get_owning_node(q).get_name(),'pin':str(P.get_pin_name(q))} for q in P.list_connected_pins(p)]
    row['pins'].append(item)
   rows.append(row)
  r['graphs'][name]=rows
 r['api']=[x for x in dir(P) if 'pin' in x or 'link' in x]
 r['compile']=B.compile_blueprint(b)
 r['status']=str(b.get_editor_property('status'))
except Exception:r['error']=traceback.format_exc()
(out/'inspection.json').write_text(json.dumps(r,indent=2),encoding='utf-8')
unreal.SystemLibrary.quit_editor()
