"""Numeric boundary contracts. Uses transient instances; never saves assets."""
import json, pathlib, sys, traceback, math
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from a09_verify import read,write,snapshot,result
import unreal
r={'tests':[]}
def check(name,condition,detail=''):
    r['tests'].append({'test':name,'passed':bool(condition),'detail':str(detail)})
    # Continue across independent numeric cases to retain all failures.
dbp=unreal.load_asset('/Game/Survival/Items/Definitions/PDA_ItemDefinition')
cbp=unreal.load_asset('/Game/Survival/Items/Catalog/PDA_GameCatalog')
gbp=unreal.load_asset('/Game/Survival/Core/BP_SurvivalGameInstance')
ibp=unreal.load_asset('/Game/Survival/Inventory/BPC_Inventory')
def definition():
    d=unreal.new_object(dbp.generated_class())
    for key,v in [('ItemId','item.audit'),('MaxStack',1),('UnitWeight',1.),('HasDurability',True),('DurabilityMax',100.)]:d.set_editor_property(key,v)
    return d
def gi_for(d):
    c=unreal.new_object(cbp.generated_class());c.set_editor_property('Items',[unreal.load_asset('/Game/Survival/Items/Definitions/DA_Item_Wood'),d])
    g=unreal.new_object(gbp.generated_class());g.set_editor_property('GameCatalog',c);g.call_method('InitializeBootstrap');return g
def new(g,limit=10.):
    o=unreal.new_object(ibp.generated_class());o.call_method('InitializeInventory',(g,4,limit));return o
try:
    for field in ('UnitWeight','DurabilityMax'):
        for label,v in [('NaN',float('nan')),('+Infinity',float('inf')),('-Infinity',-float('inf')),('negative',-1.),('zero',0.),('positive',1.)]:
            d=definition();d.set_editor_property(field,v);res=result(d.call_method('ValidateDefinition'));expected=label=='positive' or (field=='UnitWeight' and label=='zero')
            check(field+' '+label+' validation',res[0]==expected and (expected or res[1]==(4 if field=='UnitWeight' else 5)),res)
            g=gi_for(d);check(field+' '+label+' catalog readiness',g.get_editor_property('CatalogReady')==expected and g.get_editor_property('BootstrapReady')==expected)
            if not expected:
                check(field+' '+label+' clears partial lookup',len(g.get_editor_property('ItemDefinitions'))==0 and g.call_method('FindItemDefinition',('item.wood',))==(None,False),g.get_editor_property('CatalogError'))
                d.set_editor_property(field,1.);g.call_method('InitializeCatalog');check(field+' '+label+' corrected retry',g.get_editor_property('CatalogReady') and len(g.get_editor_property('ItemDefinitions'))==2)
    d=definition();d.set_editor_property('HasDurability',False);d.set_editor_property('DurabilityMax',float('nan'));check('inactive durability ignored',result(d.call_method('ValidateDefinition'))[0])
    normal=unreal.new_object(gbp.generated_class());normal.call_method('InitializeCatalog')
    for label,limit in [('NaN',float('nan')),('+Infinity',float('inf')),('-Infinity',-float('inf')),('negative',-1.),('zero',0.),('positive',10.)]:
        o=unreal.new_object(ibp.generated_class());before=snapshot(o).export_text();o.call_method('InitializeInventory',(normal,4,limit));expected=label in ('zero','positive')
        check('WeightLimit '+label,o.call_method('IsInitialized')==expected and (expected or snapshot(o).export_text()==before))
        if not expected:
            o.call_method('InitializeInventory',(normal,4,10.));check('WeightLimit '+label+' valid retry',o.call_method('IsInitialized'))
    durable=definition();durable_gi=gi_for(durable)
    for label,v in [('NaN',float('nan')),('+Infinity',float('inf')),('-Infinity',-float('inf')),('negative',-1.),('zero',0.),('maximum',100.),('above maximum',101.)]:
        o=new(durable_gi);s=read(read(snapshot(o),'Slots')[0],'ItemStack');write(s,'ItemId','item.audit');write(s,'Quantity',1);write(s,'HasDurability',True);write(s,'Durability',v);before=snapshot(o).export_text();res=result(o.call_method('TryAddExact',(s,)));expected=label in ('zero','maximum')
        check('active stack durability '+label,res[0]==expected and (expected or (res[1]==5 and snapshot(o).export_text()==before)),res)
    r['passed']=all(x['passed'] for x in r['tests'])
except Exception:r['error']=traceback.format_exc();r['passed']=False
pathlib.Path(__file__).with_name('f02_verification.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8')
assert r['passed'],r.get('error','numeric boundary failures')
