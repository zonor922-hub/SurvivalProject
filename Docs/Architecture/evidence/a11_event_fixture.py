"""Unsaved A11 listeners: cross-inventory observation, reentry and UI mirror."""
from inventory_event_fixture import listener_class as base_listener
from inventory_graph_helpers import *
def listener_class(inventory_bp):
 bp=base_listener(inventory_bp);typ=B.get_object_reference_type(inventory_bp.generated_class());snapT=type_asset('FInventorySnapshot');ints=B.get_array_type(basic('int'))
 for n,t,v in [('Other',typ,''),('OtherObserved',snapT,''),('ShownSnapshot',snapT,''),('ShownRevision',basic('int'),'-1'),('IgnoredStale',basic('int'),'0'),('EventHistory',ints,''),('AppliedHistory',ints,''),('Mode',basic('int'),'0'),('NestedError',basic('int'),'0'),('NestedSuccess',basic('bool'),'false'),('SnapshotHistory',ints,''),('AppliedEventHistory',ints,''),('LateMirror',B.get_object_reference_type(bp.generated_class()),''),('AuditOwnSnapshots',B.get_array_type(snapT),''),('AuditOtherSnapshots',B.get_array_type(snapT),'')]:var(bp,n,t,v);B.set_blueprint_variable_instance_editable(bp,n,True)
 ed=graph(bp,'OnChanged');entry=next(n for n in ed.list_all_nodes() if n.get_class().get_name()=='K2Node_FunctionEntry');rev=pin(entry,'Revision','OUTPUT');changed=pin(entry,'ChangedSlots','OUTPUT')
 e=member(ed,'EventCount',math(ed,'Add_IntInt',get(ed,'EventCount'),1),ed.find_graph_entry_pin());e=member(ed,'LastRevision',rev,e);e=member(ed,'LastChanged',changed,e);e=append(ed,e,get(ed,'EventHistory'),rev)
 sn=call(ed,own(inventory_bp,'GetSnapshot'));feed(sn,'self',get(ed,'Inventory'));wire(e,pin(sn,'execute'));s=struct(ed,'FInventorySnapshot',value(sn,'Snapshot'));sr=value(s,'Revision');e=member(ed,'ObservedRevision',sr,nextpin(sn));e=append(ed,e,get(ed,'SnapshotHistory'),sr);e=append(ed,e,get(ed,'AuditOwnSnapshots'),value(sn,'Snapshot'))
 yes,no=branch(ed,e,both(ed,math(ed,'Greater_IntInt',rev,get(ed,'ShownRevision')),math(ed,'Greater_IntInt',sr,get(ed,'ShownRevision'))))
 yes=member(ed,'ShownSnapshot',value(sn,'Snapshot'),yes);yes=member(ed,'ShownRevision',sr,yes);yes=append(ed,yes,get(ed,'AppliedHistory'),sr);yes=append(ed,yes,get(ed,'AppliedEventHistory'),rev);no=member(ed,'IgnoredStale',math(ed,'Add_IntInt',get(ed,'IgnoredStale'),1),no)
 # Both mirror branches continue with identical observation/reentry semantics.
 for end in [yes,no]:
  valid=call(ed,'/Script/Engine.KismetSystemLibrary.IsValid');feed(valid,'Object',get(ed,'Other'));observe,skip=branch(ed,end,value(valid))
  other=call(ed,own(inventory_bp,'GetSnapshot'));feed(other,'self',get(ed,'Other'));wire(observe,pin(other,'execute'));observe=member(ed,'OtherObserved',value(other,'Snapshot'),nextpin(other));observe=append(ed,observe,get(ed,'AuditOtherSnapshots'),value(other,'Snapshot'))
  reenter,_=branch(ed,observe,get(ed,'Reenter'));reenter=member(ed,'Reenter',False,reenter)
  remove,rest=branch(ed,reenter,either(ed,math(ed,'EqualEqual_IntInt',get(ed,'Mode'),1),math(ed,'EqualEqual_IntInt',get(ed,'Mode'),6)))
  n=call(ed,own(inventory_bp,'TryRemoveExact'));feed(n,'self',get(ed,'Other'));feed(n,'ItemId','item.wood');feed(n,'Quantity',1);wire(remove,pin(n,'execute'))
  late,_=branch(ed,nextpin(n),math(ed,'EqualEqual_IntInt',get(ed,'Mode'),6));again=call(ed,own(inventory_bp,'TryRemoveExact'));feed(again,'self',get(ed,'Other'));feed(again,'ItemId','item.wood');feed(again,'Quantity',1);wire(late,pin(again,'execute'));bind=call(ed,own(bp,'BindInventory'));feed(bind,'self',get(ed,'LateMirror'));feed(bind,'Target',get(ed,'Other'));wire(nextpin(again),pin(bind,'execute'))
  destroy,reverse=branch(ed,rest,math(ed,'EqualEqual_IntInt',get(ed,'Mode'),4))
  n=call(ed,'/Script/Engine.ActorComponent.K2_DestroyComponent');feed(n,'self',get(ed,'Other'));wire(destroy,pin(n,'execute'))
  ost=struct(ed,'FInventorySnapshot',value(other,'Snapshot'));n=call(ed,'/Script/Engine.KismetArrayLibrary.Array_Get');feed(n,'TargetArray',value(ost,'Slots'));feed(n,'Index',0);slot=struct(ed,'FInventorySlot',value(n,'Item'));stack=struct(ed,'FItemStack',value(slot,'ItemStack'))
  n=call(ed,own(inventory_bp,'TryTransferExact'));feed(n,'self',get(ed,'Other'));feed(n,'Destination',get(ed,'Inventory'));feed(n,'StackId',value(stack,'StackId'));feed(n,'Quantity',1)
  fresh,stale=branch(ed,reverse,math(ed,'EqualEqual_IntInt',get(ed,'Mode'),2))
  for start,stale_flag in [(fresh,False),(stale,True)]:
   callnode=n if not stale_flag else call(ed,own(inventory_bp,'TryTransferExact'))
   if stale_flag:
    feed(callnode,'self',get(ed,'Other'));feed(callnode,'Destination',get(ed,'Inventory'));feed(callnode,'StackId',value(stack,'StackId'));feed(callnode,'Quantity',1)
   feed(callnode,'ExpectedSourceRevision',math(ed,'Subtract_IntInt',value(ost,'Revision'),1) if stale_flag else value(ost,'Revision'));feed(callnode,'ExpectedDestinationRevision',sr);wire(start,pin(callnode,'execute'));answer=struct(ed,'FOperationResult',value(callnode,'Result'));convert=call(ed,'/Script/Engine.KismetMathLibrary.Conv_ByteToInt');feed(convert,'InByte',value(answer,'ErrorCode'));end=member(ed,'NestedError',value(convert),nextpin(callnode));member(ed,'NestedSuccess',value(answer,'Success'),end)
 assert B.compile_blueprint(bp);return bp
