from recons_enum import *
from recons_model import *
import fastapi
import pandas
import json
import reconexecdetailslog_getlatestexedetails
import recons_stdapi
import SourceReference_stdapi

router = fastapi.APIRouter(prefix='/recons')

@router.post('/getGlReconData', tags=['Recons'])
async def ReconsgetGlReconData(data: getGlReconDataParams):
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
    sourceref_query = {"reconId": data.reconId}
    params = framework.queryparams.QueryParams()
    params.limit = 100
    params.q = json.dumps(sourceref_query)
    
    
    finaldf = pandas.DataFrame()
    for src in reconsources:
        resp = await SourceReference_stdapi.SourceReference.get(src)
        sourceref = resp
        if not sourceref:
            continue
        srcname = sourceref.get('source', '')
        if srcname != data.sourceName:
            continue
        resp = await recons_stdapi._get_data(data.reconId, datetime.datetime.strptime(data.stmtdate,'%d-%m-%Y').strftime('%d%m%Y'), filenamemapping[data.operation], source=srcname)
        if not resp['status']:
            return {"status": resp['status'], "message": resp['message'], "data": []}
        
        # Reading the original source data
        # sourcedata = pandas.DataFrame(json.loads(resp['data']))
        feeddetails = sourceref.get('feedDetails')
        rename = {}
        df = pandas.DataFrame(resp["data"])
        for fd in feeddetails:
            if not isinstance(fd, dict):
                fd = fd.__dict__
            if fd['required']:
                rename[fd['fileColumn']] = fd['UIDisplayName']
        df.rename(columns=rename, inplace=True)
        if df.empty:
            return {"status": True, "message": "Success", "data": []}
        if data.operation == 'carry-forwardmatched':
            if 'MATCHING_STATUS' in df.columns:
                df = df[(df['MATCHING_STATUS'] == 'MATCHED')&(df['CARRY_FORWARD'] == 'Y')]
        if data.operation == 'carry-forwardunmatched':
            if 'MATCHING_STATUS' in df.columns:
                df = df[(df['MATCHING_STATUS'] == 'UNMATCHED')&(df['CARRY_FORWARD'] == 'Y')]
        # if 'System_Idx' in df.columns:
        #     del df['System_Idx']
        for col in df.columns:
            if 'link_id' in col.lower():
                df[col] = df[col].astype(str)

        finaldf = pandas.concat([finaldf, df])
        finaldf = finaldf[finaldf['GL_NUMBER'] == str(data.glnumber)]
    return {"status": True, "message": "Success", "data": finaldf.to_json(orient='records')}
