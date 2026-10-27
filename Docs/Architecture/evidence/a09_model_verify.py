import unreal,pathlib,json,sys,re,random,traceback,math,time
folder=pathlib.Path(__file__).parent;sys.path.insert(0,str(folder))
from a08_bp_helpers import B,G,P
def save(n,v): (folder/n).write_text(json.dumps(v,ensure_ascii=False,indent=2,default=str),encoding='utf-8')
def field(o,n):return re.search(r'(?<!\w)('+re.escape(n)+r'_\d+_[A-F0-9]+)=',o.export_text()).group(1)
def read(o,n):return o.get_editor_property(field(o,n))
def write(o,n,v):o.set_editor_property(field(o,n),v)
bp=unreal.load_asset('/Game/Survival/Inventory/BPC_Inventory');gi=unreal.new_object(unreal.load_asset('/Game/Survival/Core/BP_SurvivalGameInstance').generated_class());gi.call_method('InitializeCatalog')
def snap(o):return o.call_method('GetSnapshot')
def new(count=4,weight=10.):
 o=unreal.new_object(bp.generated_class());o.call_method('InitializeInventory',(gi,count,weight));return o
template=read(read(snap(new()),'Slots')[0],'ItemStack')
def add(o,id,q):
 v=template.copy() if hasattr(template,'copy') else read(read(snap(new()),'Slots')[0],'ItemStack');write(v,'ItemId',id);write(v,'Quantity',q);return o.call_method('TryAddExact',(v,))
out={'tests':[],'random_cases':0,'random_failed':[]}
def ck(n,c,d=''):out['tests'].append({'test':n,'passed':bool(c),'detail':str(d)})
try:
 rng=random.Random(270026);defs={'item.wood':(20,.5),'item.stone':(20,1.),'item.berry':(10,.1),'item.plank':(20,.4)}
 for cap,weight in ((1,0.),(4,10.),(6,100.)):
  o=new(cap,weight);model=[None]*cap;revision=0
  for step in range(200):
   id=rng.choice(list(defs)+['item.unknown']);q=rng.choice([-1,0,1,2,9,20,21,40,2147483647]);adding=rng.choice([True,False]);candidate=[list(s) if s else None for s in model];ok=id in defs and q>0
   if ok:
    remain=q;maxq,w=defs[id]
    if adding:
     if sum(defs[s[0]][1]*s[1] for s in model if s)+q*w>weight+1e-5:ok=False
     else:
      for i,s in enumerate(candidate):
       if s and s[0]==id:
        take=min(remain,maxq-s[1]);s[1]+=take;remain-=take
      for i,s in enumerate(candidate):
       if s is None and remain>0:take=min(remain,maxq);candidate[i]=[id,take];remain-=take
      ok=remain==0
    else:
     for i,s in enumerate(candidate):
      if s and s[0]==id:
       take=min(remain,s[1]);s[1]-=take;remain-=take
       if s[1]==0:candidate[i]=None
     ok=remain==0
   before=snap(o).export_text();r=add(o,id,q) if adding else o.call_method('TryRemoveExact',(id,q));after=snap(o)
   if ok:model=candidate;revision+=1
   actual=[];ids=[]
   for slot in read(after,'Slots'):
    st=read(slot,'ItemStack');actual.append([str(read(st,'ItemId')),read(st,'Quantity')] if read(slot,'HasItem') else None)
    if read(slot,'HasItem'):ids.append(read(st,'StackId').export_text())
   valid=read(r,'Success')==ok and actual==model and read(after,'Revision')==revision and read(r,'NewRevision')==revision and read(r,'ActualQuantity')==(q if ok else 0) and len(ids)==len(set(ids)) and (ok or before==after.export_text()) and math.isclose(o.call_method('GetCurrentWeight')[0],sum(defs[s[0]][1]*s[1] for s in model if s),abs_tol=1e-5)
   out['random_cases']+=1
   if not valid:out['random_failed'].append({'cap':cap,'step':step,'id':id,'q':q,'add':adding,'result':r.export_text(),'expected':model,'actual':actual})
 ck('600 model-based operations',not out['random_failed'],len(out['random_failed']))
 o=new();r=add(o,'item.wood',20);ck('exact weight boundary 10',read(r,'Success') and o.call_method('GetCurrentWeight')==(10.,True));before=snap(o).export_text();r=add(o,'item.berry',1);ck('one above weight rejects unchanged',not read(r,'Success') and snap(o).export_text()==before)
except Exception:out['error']=traceback.format_exc()
out['passed']=not out['random_failed'] and all(x['passed'] for x in out['tests']) and 'error' not in out
save('a09_model_verification.json',out)
assert out['passed'],out.get('error',out['random_failed'])