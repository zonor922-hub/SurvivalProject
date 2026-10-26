"""A06 catalog contract tests using transient GameInstances and catalogs."""
import unreal,json,pathlib,traceback
r={'tests':[]};out=pathlib.Path(__file__).resolve().with_name('a06_verification.json')
try:
 gi_bp=unreal.load_asset('/Game/Survival/Core/BP_SurvivalGameInstance');cat_bp=unreal.load_asset('/Game/Survival/Items/Catalog/PDA_GameCatalog');def_bp=unreal.load_asset('/Game/Survival/Items/Definitions/PDA_ItemDefinition')
 r['engine_version']=unreal.SystemLibrary.get_engine_version()
 r['project_directory']=unreal.Paths.project_dir()
 r['compile']={}
 for path in ('/Game/Survival/Core/BP_SurvivalGameInstance','/Game/Survival/Core/BP_SurvivalPlayerController','/Game/Survival/Items/Catalog/PDA_GameCatalog','/Game/Survival/Items/Definitions/PDA_ItemDefinition'):
  blueprint=unreal.load_asset(path)
  assert blueprint and unreal.BlueprintEditorLibrary.compile_blueprint(blueprint),path
  status=str(blueprint.get_editor_property('status'));r['compile'][path]=status
  assert 'BS_UP_TO_DATE' in status,path
 catalog=unreal.load_asset('/Game/Survival/Items/Catalog/DA_GameCatalog');wood=unreal.load_asset('/Game/Survival/Items/Definitions/DA_Item_Wood')
 def check(label,condition,detail=''):
  r['tests'].append({'test':label,'passed':bool(condition),'detail':str(detail)});assert condition,label
 def newgi(cat):
  o=unreal.new_object(gi_bp.generated_class());o.set_editor_property('GameCatalog',cat);return o
 o=newgi(catalog);o.call_method('InitializeBootstrap');check('bootstrap catalog ready',o.get_editor_property('BootstrapReady') and o.get_editor_property('CatalogReady'));check('four definitions',len(o.get_editor_property('ItemDefinitions'))==4)
 for ident in ('item.wood','item.stone','item.berry','item.plank'):
  found=o.call_method('FindItemDefinition',(ident,));check('resolve '+ident,found[1] and str(found[0].get_editor_property('ItemId'))==ident,found)
 found=o.call_method('FindItemDefinition',('item.unknown',));check('unknown safe',found==(None,False),found)
 before=dict(o.get_editor_property('ItemDefinitions'));o.call_method('InitializeCatalog');o.call_method('InitializeBootstrap');check('idempotent init',dict(o.get_editor_property('ItemDefinitions'))==before and o.get_editor_property('InitializeCount')==1)
 bad=unreal.new_object(def_bp.generated_class());bad.set_editor_property('ItemId','item.bad');bad.set_editor_property('MaxStack',0)
 for label,items,expected in [('duplicate',[wood,wood],'DuplicateItemId'),('missing',[wood,None],'DefinitionMissing'),('invalid',[wood,bad],'InvalidDefinition')]:
  c=unreal.new_object(cat_bp.generated_class());c.set_editor_property('Items',items);x=newgi(c);x.call_method('InitializeBootstrap')
  check(label+' blocks readiness',not x.get_editor_property('CatalogReady') and not x.get_editor_property('BootstrapReady'))
  check(label+' clears partial lookup',len(x.get_editor_property('ItemDefinitions'))==0)
  check(label+' diagnostic',str(x.get_editor_property('CatalogError')).startswith(expected),x.get_editor_property('CatalogError'))
  check(label+' lookup safe',x.call_method('FindItemDefinition',('item.wood',))==(None,False))
  x.set_editor_property('GameCatalog',catalog);x.call_method('InitializeCatalog');check(label+' explicit retry',x.get_editor_property('CatalogReady') and len(x.get_editor_property('ItemDefinitions'))==4)
 x=newgi(None);x.call_method('InitializeCatalog');check('missing catalog rejected',not x.get_editor_property('CatalogReady') and x.get_editor_property('CatalogError')=='CatalogMissing')
 r['passed']=True
except Exception:r['error']=traceback.format_exc();r['passed']=False
out.write_text(json.dumps(r,indent=2,ensure_ascii=False),encoding='utf-8')
