from recons_enum import *
from recons_model import *
import fastapi
import pandas
import json
import numpy
import recons_stdapi

router = fastapi.APIRouter(prefix='/recons')

@router.post('/operationData', tags=['Recons'])
async def ReconsoperationData(params: operationDataParams):
    # data = pandas.DataFrame(json.loads(data.records))
    tableName = params.reconId
    if params.operation in ['matched', 'rollbackwaiting', 'selfmatched', 'carry-forwardmatched']:
        tableName = f'{params.reconId}_matched'
    if params.operation in ['unmatched', 'authwaiting', 'carry-forwardunmatched']:
        tableName = f'{params.reconId}_unmatched'
    data = await recons_stdapi.getBulkRecords(params.records, tableName)
    if 'Json Data' in data.columns:
        data = data.join(pandas.json_normalize(data['Json Data'])).drop(columns=['Json Data'])
    data = data.drop_duplicates(keep='first')
    data['Count'] = 1
    amt_col = "DC_AMOUNT"
    if "AMOUNT" in data.columns:
        amt_col = "AMOUNT"
    if amt_col not in data.columns:
        return {"status": False, "message": f"{amt_col} Column not found", "data": []}
    data['Amount'] = data[[amt_col]].fillna(0.0).sum(axis=1)
    
    if 'Dr/Cr' in data.columns:
        data['Cr Count'] = data[data['Dr/Cr'].str.lower() == 'cr'][['Dr/Cr']].fillna(0).count(axis=1)
        data['Dr Count'] = data[data['Dr/Cr'].str.lower() == 'dr'][['Dr/Cr']].fillna(0).count(axis=1)
        data['Cr Amount'] = data[data['Dr/Cr'].str.lower() == 'cr'][[amt_col]].fillna(0.0).sum(axis=1)
        data['Dr Amount'] = data[data['Dr/Cr'].str.lower() == 'dr'][[amt_col]].fillna(0.0).sum(axis=1)
        data['Cr Amount'] = data['Cr Amount'].fillna(0).astype(numpy.float64)
        data['Dr Amount'] = data['Dr Amount'].fillna(0).astype(numpy.float64)
        data['Amount'] = data['Amount'].fillna(0).astype(numpy.float64)
        final_df = pandas.pivot_table(data, index=['SOURCE'], values=['Count', 'Amount','Cr Count', 'Cr Amount','Dr Count','Dr Amount'], aggfunc=numpy.sum).reset_index()
        final_df = final_df[['SOURCE', 'Count', 'Amount','Cr Count', 'Cr Amount','Dr Count','Dr Amount']]
    elif 'Dr/Cr Ind' in data.columns:
        data['Cr Count'] = data[data['Dr/Cr Ind'].str.lower().isin(['cr', 'c'])][['Dr/Cr Ind']].fillna(0).count(axis=1)
        data['Dr Count'] = data[data['Dr/Cr Ind'].str.lower().isin(['dr', 'd'])][['Dr/Cr Ind']].fillna(0).count(axis=1)
        data['Cr Amount'] = data[data['Dr/Cr Ind'].str.lower().isin(['cr', 'c'])][[amt_col]].fillna(0.0).sum(axis=1)
        data['Dr Amount'] = data[data['Dr/Cr Ind'].str.lower().isin(['dr', 'd'])][[amt_col]].fillna(0.0).sum(axis=1)
        data['Cr Amount'] = data['Cr Amount'].fillna(0).astype(numpy.float64)
        data['Dr Amount'] = data['Dr Amount'].fillna(0).astype(numpy.float64)
        data['Amount'] = data['Amount'].fillna(0).astype(numpy.float64)
        final_df = pandas.pivot_table(data, index=['SOURCE'], values=['Count', 'Amount','Cr Count', 'Cr Amount','Dr Count','Dr Amount'], aggfunc=numpy.sum).reset_index()
        final_df = final_df[['SOURCE', 'Count', 'Amount','Cr Count', 'Cr Amount','Dr Count','Dr Amount']]
    else:
        data['Amount'] = data['Amount'].fillna(0).astype(numpy.float64)
        final_df = pandas.pivot_table(data, index=['SOURCE'], values=['Count', 'Amount'], aggfunc=numpy.sum).reset_index()
        final_df['Cr Count'] = 0
        final_df['Dr Count'] = 0
        final_df['Cr Amount'] = 0.0
        final_df['Dr Amount'] = 0.0
        final_df = final_df[['SOURCE', 'Count', 'Amount','Cr Count', 'Cr Amount','Dr Count','Dr Amount']]
    return {"status": True, "message": "Success", "data":final_df.to_json(orient='records')}
