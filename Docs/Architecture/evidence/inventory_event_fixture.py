"""Unsaved Blueprint listener proves dispatcher semantics using runtime Blueprint bindings."""
import time
from inventory_graph_helpers import *

def listener_class(inventory_bp):
    bp=B.create_blueprint_asset_with_parent('/Game/__InventoryContractTests/Listener'+str(time.time_ns()),unreal.Object)
    typ=B.get_object_reference_type(inventory_bp.generated_class());ints=B.get_array_type(basic('int'))
    for n,t,default in [('Inventory',typ,''),('EventCount',basic('int'),'0'),('LastRevision',basic('int'),'0'),('ObservedRevision',basic('int'),'0'),('LastChanged',ints,''),('Reenter',basic('bool'),'false')]:var(bp,n,t,default)
    B.set_blueprint_variable_instance_editable(bp,'Reenter',True)
    ed=graph(bp,'OnChanged');revision=ed.add_graph_input_parameter('Revision',basic('int'));changed=ed.add_graph_input_parameter('ChangedSlots',ints)
    entry=member(ed,'EventCount',math(ed,'Add_IntInt',get(ed,'EventCount'),1),ed.find_graph_entry_pin())
    entry=member(ed,'LastRevision',revision,entry);entry=member(ed,'LastChanged',changed,entry)
    snap=call(ed,own(inventory_bp,'GetSnapshot'));wire(get(ed,'Inventory'),pin(snap,'self'));wire(entry,pin(snap,'execute'))
    br=struct(ed,'FInventorySnapshot',value(snap,'Snapshot'));entry=member(ed,'ObservedRevision',value(br,'Revision'),nextpin(snap))
    yes,_=branch(ed,entry,get(ed,'Reenter'));yes=member(ed,'Reenter',False,yes)
    remove=call(ed,own(inventory_bp,'TryRemoveExact'));wire(get(ed,'Inventory'),pin(remove,'self'));lit(remove,'ItemId','item.wood');lit(remove,'Quantity',1);wire(yes,pin(remove,'execute'))
    assert B.compile_blueprint(bp)
    ed=graph(bp,'BindInventory');target=ed.add_graph_input_parameter('Target',typ)
    entry=member(ed,'Inventory',target,ed.find_graph_entry_pin())
    action=next(str(a) for a in ed.list_available_nodes([target]) if str(a).endswith('|BindEventtoOnInventoryChanged'))
    bind=ed.create_node_from_name(action,unreal.Vector2D(0,0),[target]);wire(target,pin(bind,'self'));wire(entry,pin(bind,'execute'))
    dp=pin(bind,'Delegate');action=next(str(a) for a in ed.list_available_nodes([dp]) if str(a).endswith('|Создатьсобытие') or str(a).endswith('|CreateEvent'))
    delegate=ed.create_node_from_name(action,unreal.Vector2D(0,0),[dp])
    # Context-based creation connects the output; explicitly ensure it when needed.
    outs=[p for p in B.list_all_pins(delegate) if 'OUTPUT' in str(P.get_pin_direction(p))]
    assert len(outs)==1;wire(outs[0],dp);B.set_create_delegate_function(delegate,'OnChanged')
    assert B.compile_blueprint(bp)
    return bp

