"""Unsaved Object Blueprint receiver; optional A10 commands after commit only."""
from inventory_event_fixture import listener_class as base_listener
from inventory_graph_helpers import *

def listener_class(inventory_bp):
    bp=base_listener(inventory_bp)
    var(bp,'ReenterMode',basic('int'),'0');B.set_blueprint_variable_instance_editable(bp,'ReenterMode',True)
    ed=graph(bp,'OnChanged');entry_node=next(n for n in ed.list_all_nodes() if n.get_class().get_name()=='K2Node_FunctionEntry')
    revision=pin(entry_node,'Revision','OUTPUT');changed=pin(entry_node,'ChangedSlots','OUTPUT')
    entry=member(ed,'EventCount',math(ed,'Add_IntInt',get(ed,'EventCount'),1),ed.find_graph_entry_pin())
    entry=member(ed,'LastRevision',revision,entry);entry=member(ed,'LastChanged',changed,entry)
    snap=call(ed,own(inventory_bp,'GetSnapshot'));wire(get(ed,'Inventory'),pin(snap,'self'));wire(entry,pin(snap,'execute'))
    state=struct(ed,'FInventorySnapshot',value(snap,'Snapshot'));entry=member(ed,'ObservedRevision',value(state,'Revision'),nextpin(snap))
    yes,_=branch(ed,entry,get(ed,'Reenter'));yes=member(ed,'Reenter',False,yes)
    def item(index):
        n=call(ed,'/Script/Engine.KismetArrayLibrary.Array_Get');wire(value(state,'Slots'),pin(n,'TargetArray'));feed(n,'Index',index)
        slot=struct(ed,'FInventorySlot',value(n,'Item'));return struct(ed,'FItemStack',value(slot,'ItemStack'))
    first,second=item(0),item(1)
    merge,split=branch(ed,yes,math(ed,'EqualEqual_IntInt',get(ed,'ReenterMode'),1))
    n=call(ed,own(inventory_bp,'TryMerge'));wire(get(ed,'Inventory'),pin(n,'self'));feed(n,'SourceStackId',value(second,'StackId'));feed(n,'TargetStackId',value(first,'StackId'));wire(merge,pin(n,'execute'))
    n=call(ed,own(inventory_bp,'TrySplit'));wire(get(ed,'Inventory'),pin(n,'self'));feed(n,'StackId',value(first,'StackId'));feed(n,'Quantity',4);feed(n,'TargetSlot',1);wire(split,pin(n,'execute'))
    assert B.compile_blueprint(bp)
    return bp
