"""Input validation and transactional domain operations, independent of HTTP."""
from datetime import datetime,date
from decimal import Decimal,InvalidOperation
from dal.database import MODELS,save,delete

def validate(table,data):
 if table not in MODELS:raise ValueError('Unknown relation')
 m=MODELS[table];out={}
 for k,v in data.items():
  if k not in m['fields']:raise ValueError('Unknown field: '+k)
  if v is None or str(v).strip()=='':
   if k not in m['optional']:raise ValueError(k+' is required')
   out[k]=None;continue
  v=str(v).strip()
  if len(v)>4000:raise ValueError(k+' is too long')
  if k.endswith('Id') or k=='ModelYear':
   try:v=int(v)
   except ValueError:raise ValueError(k+' must be an integer')
  elif k in ['MeasuredValue','BenefitValue','SalePrice','RentalCharge']:
   try:
    d=Decimal(v)
    if not d.is_finite():raise InvalidOperation
    v=str(d)
   except InvalidOperation:raise ValueError(k+' must be a finite number')
  elif k.endswith('At'):
   try:
    datetime.strptime(v,'%Y-%m-%dT%H:%M:%SZ')
    if len(v)!=20:raise ValueError()
   except ValueError:raise ValueError(k+' requires UTC YYYY-MM-DDTHH:MM:SSZ')
  elif k in ['ValidFrom','ValidTo','EffectiveFrom','EffectiveTo','ActiveFrom','ActiveTo','PeriodStart','PeriodEnd','QualificationDate']:
   try:
    date.fromisoformat(v)
    if len(v)!=10:raise ValueError()
   except ValueError:raise ValueError(k+' requires YYYY-MM-DD')
  out[k]=v
 return out

def mutate(c,table,data=None,row_id=None,operation='save'):
 with c:
  if operation=='delete':
   if table=='VehicleActivity':
    old=c.execute('SELECT * FROM VehicleActivity WHERE Id=?',(row_id,)).fetchone()
    if not old:raise ValueError('Record no longer exists')
    delete(c,table,row_id);delete(c,old['ActivityKind'],old[old['ActivityKind']+'Id'])
   else:delete(c,table,row_id)
   return row_id
  if table in ['EventAward','PeriodAward'] and not row_id:
   component=data.pop('_component',{})
   parent=validate(table,data);parent['FirstComponentId']=-1
   id=save(c,table,parent);component[table+'Id']=id
   cid=save(c,table+'Component',validate(table+'Component',component))
   c.execute(f'UPDATE {table} SET FirstComponentId=? WHERE Id=?',(cid,id));return id
  if table=='VehicleActivity' and not row_id:
   # Parent and exactly one subtype commit atomically through deferred composite FKs.
   kind=data.get('ActivityKind')
   if kind not in ['Sale','Rental','Service']:raise ValueError('Choose Sale, Rental or Service')
   child=data.pop('_subtype',{})
   parent=validate(table,data);parent[kind+'Id']=-1
   id=save(c,table,parent);child['VehicleActivityId']=id
   sid=save(c,kind,validate(kind,child));c.execute(f'UPDATE VehicleActivity SET {kind}Id=? WHERE Id=?',(sid,id));return id
  if table=='VehicleActivity' and row_id:
   old=c.execute('SELECT ActivityKind FROM VehicleActivity WHERE Id=?',(row_id,)).fetchone()
   if old and data.get('ActivityKind',old[0])!=old[0]:raise ValueError('Activity kind cannot change; create another activity')
  return save(c,table,validate(table,data),row_id)
