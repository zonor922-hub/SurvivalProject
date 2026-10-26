"""A05 repeatable validation tests. Invalid cases use transient objects only."""
import unreal,json,pathlib,traceback,math
B=unreal.BlueprintEditorLibrary;r={'tests':[],'schemas':{},'items':[]};out=pathlib.Path(__file__).resolve().with_name('a05_verification.json')
try:
 bp=unreal.load_asset('/Game/Survival/Items/Definitions/PDA_ItemDefinition')
 assert bp is not None
 assert B.compile_blueprint(bp), 'Blueprint compilation failed'
 assert 'BS_UP_TO_DATE' in str(bp.get_editor_property('status'))
 r['engine_version']=unreal.SystemLibrary.get_engine_version()
 r['project_directory']=unreal.Paths.project_dir()
 err=unreal.get_type_from_enum(unreal.load_asset('/Game/Survival/Items/Types/EOperationError'))
 def checked(label,obj,ok,code):
  result=obj.call_method('ValidateDefinition');vals=result.to_tuple();text=result.export_text()
  # Reflected UDS field order is stable in this resource and independently checked below.
  actual=(result.get_editor_property('Success_1_2A80304A4EA00C576412AD8566A6FA88'),result.get_editor_property('ErrorCode_4_A39592FC42717FE0DDAEE2BAFFC5DACE').value,result.get_editor_property('ActualQuantity_7_379D907F4B3C15B2AA2297B7E278E2BE'),result.get_editor_property('NewRevision_9_CAD0A43D4531954479F79C882B90A3C6'))
  passed=actual==(ok,code,0,0);r['tests'].append({'test':label,'passed':passed,'result':text});assert passed,label
 def fresh():
  o=unreal.new_object(bp.generated_class());o.set_editor_property('ItemId','item.test');o.set_editor_property('MaxStack',20);o.set_editor_property('UnitWeight',0.5);return o
 for name,ident,stack,weight in [('Wood','item.wood',20,0.5),('Stone','item.stone',20,1),('Berry','item.berry',10,0.1),('Plank','item.plank',20,0.4)]:
  a=unreal.load_asset('/Game/Survival/Items/Definitions/DA_Item_'+name);checked('valid '+name,a,True,1)
  assert str(a.get_editor_property('ItemId'))==ident;assert a.get_editor_property('MaxStack')==stack;assert math.isclose(a.get_editor_property('UnitWeight'),weight,rel_tol=1e-6)
  r['items'].append({'path':a.get_path_name(),'id':ident,'max_stack':stack,'unit_weight':weight,'category':str(a.get_editor_property('Category'))})
 for label,fields,code in [('empty ID',{'ItemId':'None'},2),('zero stack',{'MaxStack':0},3),('negative stack',{'MaxStack':-1},3),('negative weight',{'UnitWeight':-0.1},4),('zero durability',{'HasDurability':True,'DurabilityMax':0,'MaxStack':1},5),('durable stack',{'HasDurability':True,'DurabilityMax':100,'MaxStack':2},5)]:
  o=fresh()
  for k,v in fields.items():o.set_editor_property(k,v)
  checked(label,o,False,code)
 o=fresh();o.set_editor_property('UnitWeight',0);o.set_editor_property('MaxStack',1);checked('zero weight allowed',o,True,1)
 o.set_editor_property('HasDurability',True);o.set_editor_property('DurabilityMax',100);checked('valid durability',o,True,1)
 before=str(o.get_editor_property('ItemId'));o.set_editor_property('DisplayName','Переименованный предмет');assert str(o.get_editor_property('ItemId'))==before;checked('rename preserves ID',o,True,1)
 for n in ('FItemStack','FInventorySlot','FInventorySnapshot','FOperationResult'):
  s=json.loads(B.pin_type_to_json_schema(B.get_struct_type(unreal.load_asset('/Game/Survival/Items/Types/'+n)),None));r['schemas'][n]=s
 assert r['schemas']['FItemStack']['properties']['durability']['type']=='number'
 assert r['schemas']['FInventorySnapshot']['properties']['slots']['type']=='array'
 assert r['schemas']['FInventorySnapshot']['properties']['maxWeight']['type']=='number'
 expected={'FItemStack':{'stackId','itemId','quantity','durability','hasDurability'},'FInventorySlot':{'slotIndex','itemStack','hasItem'},'FInventorySnapshot':{'inventoryId','revision','slots','maxWeight'},'FOperationResult':{'success','errorCode','actualQuantity','newRevision'}}
 for n,fields in expected.items():
  assert set(r['schemas'][n]['properties'])==fields, (n,r['schemas'][n])
  schema_text=json.dumps(r['schemas'][n]).lower()
  assert not any(token in schema_text for token in ('/script/umg','userwidget','widgetblueprint')),n
 default=unreal.new_object(bp.generated_class()).call_method('ValidateDefinition')
 assert not default.get_editor_property('Success_1_2A80304A4EA00C576412AD8566A6FA88')
 r['definition_types']={str(n):B.get_member_variable_type(bp,n).export_text() for n in B.list_member_variable_names(bp,False)}
 assert 'softobject' in r['definition_types']['Icon'] and 'Texture2D' in r['definition_types']['Icon']
 assert 'softobject' in r['definition_types']['WorldMesh'] and 'StaticMesh' in r['definition_types']['WorldMesh']
 r['compile']=str(bp.get_editor_property('status'));r['passed']=True
except Exception:r['error']=traceback.format_exc();r['passed']=False
out.write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8')

