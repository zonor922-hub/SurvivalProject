"""Reusable helpers for scoped Blueprint graph authoring through UE APIs."""
import unreal
B=unreal.BlueprintEditorLibrary;G=unreal.BlueprintGraphEditor;P=unreal.BlueprintGraphPinLibrary
def pin(n,name,d=None):
 ps=[p for p in B.list_all_pins(n) if (str(P.get_pin_name(p))==name or str(P.get_pin_name(p)).startswith(name+'_')) and (d is None or d in str(P.get_pin_direction(p)))]
 assert len(ps)==1,(n.get_name(),name,[str(P.get_pin_name(p)) for p in B.list_all_pins(n)]);return ps[0]
def wire(a,b):assert P.try_create_connection(a,b),(a,b)
def lit(n,name,value):assert P.set_pin_value(pin(n,name,'INPUT'),str(value)),(name,value)
def call(ed,fn):
 n=ed.add_call_function_node(fn);assert n,fn;return n
def graph(bp,name,clear=True):
 ed=G.get_graph_editor_by_name(bp,name) if B.find_graph(bp,name) else G.create_and_edit_function_graph(bp,name)
 if clear:
  for n in ed.list_comment_nodes():ed.remove_comment_node(n)
  ed.remove_nodes([n for n in ed.list_all_nodes() if n.get_class().get_name()!='K2Node_FunctionEntry'])
 return ed
def basic(n):return B.get_basic_type_by_name(n)
def var(bp,n,t,v=''):
 if n not in [str(x) for x in B.list_member_variable_names(bp,False)]:assert G.get_graph_editor_by_name(bp,'EventGraph').add_member_variable(n,t,v),n
 B.set_blueprint_variable_category(bp,n,'Catalog')
def get(ed,n,cls=None,obj=None):
 node=ed.add_get_member_variable_node(n,(cls.static_class().get_path_name() if isinstance(cls,type) else cls.get_path_name()) if cls else '');assert node,n
 if obj:wire(obj,pin(node,'self'))
 return pin(node,n,'OUTPUT')
def setv(ed,n,v=None):
 node=ed.add_set_member_variable_node(n);assert node,n
 if v is not None:lit(node,n,v)
 return node
def chain(a,b,out='then'):wire(pin(a,out,'OUTPUT'),pin(b,'execute','INPUT'))
def layout(ed):
 for i,n in enumerate(ed.list_all_nodes()):B.set_node_pos(n,unreal.IntPoint((i%5)*400,(i//5)*280))
def own(bp,n):return bp.generated_class().get_path_name()+':'+n
def compile_save(bp):
 assert B.compile_blueprint(bp),bp.get_name();assert 'BS_UP_TO_DATE' in str(bp.get_editor_property('status'));unreal.EditorAssetLibrary.save_loaded_asset(bp)
