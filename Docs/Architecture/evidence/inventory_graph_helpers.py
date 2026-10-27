"""Editor-only graph authoring helpers; generated Blueprint runs without Python."""
from a08_bp_helpers import *

def value(node, name='ReturnValue'): return pin(node,name,'OUTPUT')
def feed(node,name,v):
    if isinstance(v,(str,int,float,bool)): lit(node,name,str(v).lower() if isinstance(v,bool) else v)
    else: wire(v,pin(node,name,'INPUT'))
def math(ed,fn,a,b=None):
    n=call(ed,'/Script/Engine.KismetMathLibrary.'+fn);feed(n,'A',a)
    if b is not None:feed(n,'B',b)
    return value(n)
def both(ed,*conditions):
    result=conditions[0]
    for c in conditions[1:]:result=math(ed,'BooleanAND',result,c)
    return result
def either(ed,a,b):return math(ed,'BooleanOR',a,b)
def negate(ed,a):return math(ed,'Not_PreBool',a)
def struct(ed,name,source=None,**fields):
    action=next(str(a) for a in ed.list_available_nodes([]) if str(a).endswith('|'+('Break' if source is not None else 'Make')+name))
    n=ed.create_node_from_name(action,unreal.Vector2D(0,0),[]);assert n
    if source is not None:wire(source,pin(n,name,'INPUT'))
    for k,v in fields.items():feed(n,k,v)
    return n
def local(ed,name,typ,default=''):
    ed.add_local_variable(name,typ,default)
def lg(ed,name):return value(ed.add_get_local_variable_node(name),name)
def ls(ed,name,source,entry):
    n=ed.add_set_local_variable_node(name);feed(n,name,source);wire(entry,pin(n,'execute'));return value(n,'then')
def member(ed,name,source,entry):
    n=setv(ed,name);feed(n,name,source);wire(entry,pin(n,'execute'));return value(n,'then')
def branch(ed,entry,condition):
    n=ed.add_branch_node();wire(entry,pin(n,'execute'));wire(condition,pin(n,'Condition'));return value(n,'then'),value(n,'else')
def each(ed,entry,array):
    n=ed.create_node_from_name('Utilities|Array|ForEachLoop',unreal.Vector2D(0,0),[]);wire(array,pin(n,'Array'));wire(entry,pin(n,'Exec'));return n
def aset(ed,entry,array,index,item):
    n=call(ed,'/Script/Engine.KismetArrayLibrary.Array_Set');wire(array,pin(n,'TargetArray'));wire(item,pin(n,'Item'));feed(n,'Index',index);wire(entry,pin(n,'execute'));return value(n,'then')
def append(ed,entry,array,item):
    n=call(ed,'/Script/Engine.KismetArrayLibrary.Array_AddUnique');wire(array,pin(n,'TargetArray'));wire(item,pin(n,'NewItem'));wire(entry,pin(n,'execute'));return value(n,'then')
def ret(ed,entry,**fields):
    n=ed.add_return_node()
    for k,v in fields.items():feed(n,k,v)
    wire(entry,pin(n,'execute'));return n
def output(ed,**types):
    for n,t in types.items():ed.add_graph_output_parameter(n,t)
def method(ed,bp,name,entry=None,**args):
    n=call(ed,own(bp,name))
    for k,v in args.items():feed(n,k,v)
    if entry is not None:wire(entry,pin(n,'execute'))
    return n
def nextpin(n):return value(n,'then')
def guid(ed):return value(call(ed,'/Script/Engine.KismetGuidLibrary.NewGuid'))
def type_asset(name):return B.get_struct_type(unreal.load_asset('/Game/Survival/Items/Types/'+name))
