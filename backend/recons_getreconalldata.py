from recons_enum import *
from recons_model import *
import fastapi
import pandas
import json
import reconexecdetailslog_getlatestexedetails
import recons_stdapi
import SourceReference_stdapi

router = fastapi.APIRouter(prefix='/recons')

@router.post('/getReconAllData', tags=['Recons'])
async def ReconsgetReconAllData(data: getReconAllDataParams):
    if not data.stmtdate:
        data1 = reconexecdetailslog_getlatestexedetails.getLatestExeDetailsParams
        data1.reconId = data.reconId
        doc = await reconexecdetailslog_getlatestexedetails.ReconExecDetailsLoggetLatestExeDetails(data1)
        if doc['status']:
            data.stmtdate = doc["data"][0].get('statementDate', None).strftime('%d-%m-%Y')
        else:
            return {"status": False, "message": "No Latest Execution Found", "data": []}
        
    filenamemapping = {'matched': 'matched', 'unmatched': 'unmatched', 'authwaiting': 'authwaiting',
            'rollbackwaiting': 'rollbackwaiting', 'reversal': 'selfmatched', 'carry-forwardmatched': 'matched',
            'carry-forwardunmatched': 'unmatched'}

    # fetch recon data
    recondata = await recons_stdapi.Recons.get(data.reconId)
    recondata = recondata
    if not recondata:
        return {"status": False, "message":"Unable to find recon details", "data": []}
    reconsources = recondata.get('sources', [])
    if not reconsources:
        return {"status": False, "message": "Sources are not configured.", "data": []}
    sources = []
    for src in reconsources:
        resp = await SourceReference_stdapi.SourceReference.get(src)
        sourceref = resp
        if not sourceref:
            continue
        sources.append(sourceref.get('source', ''))
    
    
    finaldf = pandas.DataFrame()
    resp = await recons_stdapi._get_data(data.reconId, datetime.datetime.strptime(data.stmtdate,'%d-%m-%Y').strftime('%d%m%Y'), filenamemapping[data.operation])
    
    pagination = False
    # if data.reconId == '65c5b8328b611e59650eea2e':
    # resp = await recons_stdapi._get_data_duckdb(
    #     data.reconId, 
    #     datetime.datetime.strptime(data.stmtdate,'%d-%m-%Y').strftime('%d%m%Y'), 
    #     filenamemapping[data.operation],
    #     limit=data.limit,
    #     offset=data.offset,
    #     source=sources
    # )
    pagination = resp.get("pagination", False)
    
    if not resp['status']:
        return {"status": resp['status'], "message": resp['message'], "data": []}
    
    # Reading the original source data
    # df = pandas.DataFrame(resp["data"])
    
    if not isinstance(resp["data"], pandas.DataFrame):
        df = pandas.DataFrame(resp["data"])
    else:
        df = resp["data"].copy()
    
    if not df.empty:
        if '__index_level_0_' in df.columns.tolist():
            del df['__index_level_0_']
        if '__index_level_0__' in df.columns.tolist():
            del df['__index_level_0__']
        if 'level_0' in df.columns.tolist():
            del df['level_0']
        if 'index' in df.columns.tolist():
            del df['index']
        # df = df.reset_index()
        # print(df['Json Data'])
        # df['Json Data'] = df['Json Data'].apply(json.dumps)
        # print(df['Json Data'])
        # df['Json Data'] = df['Json Data'].astype(str)
        # df['Json Data'] = df['Json Data'].apply(eval)
        # print(df['Json Data'])
        print(datetime.datetime.now())
        # df = df.join(pandas.json_normalize(df['Json Data'])).drop(columns=['Json Data'])
        # df = pandas.concat([df, pandas.json_normalize(df['Json Data'])], axis=1)
        # print(df)
        # print(df.columns)
        # print(df['DC_AMOUNT'])
        if data.operation == 'carry-forwardmatched':
            if 'MATCHING_STATUS' in df.columns:
                df = df[(df['MATCHING_STATUS'] == 'MATCHED')&(df['CARRY_FORWARD'] == 'Y')]
        if data.operation == 'carry-forwardunmatched':
            if 'MATCHING_STATUS' in df.columns:
                df = df[(df['MATCHING_STATUS'] == 'UNMATCHED')&(df['CARRY_FORWARD'] == 'Y')]
        
        
        # for col in df.columns:
        #     if 'link_id' in col.lower():
        #         df[col] = df[col].astype(str)
        print(datetime.datetime.now())
    # return {"status": True, "message": "Success", "data": df.to_json(orient='records'), "old_scroll_id": resp.get("old_scroll_id", "")}
    # print(df['DC_AMOUNT'])
    # print('data columns :',df.columns.tolist())
    if "" in df.columns:
        df = df.drop([""], axis=1)
    df = df.drop([''], errors='ignore')
    print("df: ", df)
    print('Data columns :',df.columns.tolist())
    return {
        "status": True, 
        "message": "Success", 
        "data": df.to_json(orient='records'), 
        # "data": df.to_dicts(),
        "old_scroll_id": resp.get("old_scroll_id", ""),
        "limit": data.limit,
        "offset": data.offset,
        "pagination": pagination
    }

    #if data.operation == 'carry-forwardmatched':
    #    if 'MATCHING_STATUS' in df.columns:
    #        df = df[(df['MATCHING_STATUS'] == 'MATCHED')&(df['CARRY_FORWARD'] == 'Y')]
    #if data.operation == 'carry-forwardunmatched':
    #    if 'MATCHING_STATUS' in df.columns:
    #        df = df[(df['MATCHING_STATUS'] == 'UNMATCHED')&(df['CARRY_FORWARD'] == 'Y')]
    #for col in df.columns:
    #    if 'link_id' in col.lower():
    #        df[col] = df[col].astype(str)
    #
    #return {"status": True, "message": "Success", "data": df.to_json(orient='records'), "old_scroll_id": resp.get("old_scroll_id", "")}
