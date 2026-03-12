from recons_enum import *
from recons_model import *
import fastapi
import json
import os
import pandas
import datetime
import reconexecdetailslog_getlatestexedetails
import SourceReference_stdapi

router = fastapi.APIRouter(prefix='/recons')

@router.post('/downloadForceMatchRecords', tags=['Recons'])
async def ReconsdownloadForceMatchRecords(data: downloadForceMatchRecordsParams):
    if not data.stmtdate:
        data1 = reconexecdetailslog_getlatestexedetails.getLatestExeDetailsParams
        data1.reconId = data.reconId
        doc = await reconexecdetailslog_getlatestexedetails.ReconExecDetailsLoggetLatestExeDetails(data1)
        if doc['status']:
            data.stmtdate = doc["data"][0].get('statementDate', None).strftime('%d-%m-%Y')
        else:
            return {"status": False, "message": "No Latest Execution Found", "data": []}

    query = {"reconId": data.reconId}
    params = framework.queryparams.QueryParams()
    params.limit = 100
    params.skip = 0
    params.q = json.dumps(query)
    sourceins = SourceReference_stdapi.SourceReference()
    resp = await sourceins.get_all(params, framework.settings.dbName)
    resp = resp.get('data', [])
    sourceName = []
    for each_source_ref in resp:
        sourceName.append(each_source_ref['source'])
    outputPath = os.path.join(framework.settings.mftpath, 'OUTPUT', data.reconId, datetime.datetime.strptime(data.stmtdate, '%d-%m-%Y').strftime('%d%m%Y'))
    df = pandas.DataFrame()
    for each_source in sourceName:
        if data.isMatched:
            fileName = ".csv"
        else:
            fileName = "_UnMatched.csv"
        if os.path.exists(os.path.join(outputPath, each_source + fileName)):
            un_match_df = pandas.read_csv(os.path.join(outputPath, each_source + fileName), dtype=str)
            # df = df.append(un_match_df)
            df = pandas.concat([df,un_match_df])
            del un_match_df
    df = df.reset_index(drop=True)
    data_col = []
    source_list = []
    for each_data in data.sourceColumns:
        print(each_data)
        each_data = each_data.__dict__
        data_col += each_data['Columns']
        source_list.append(each_data['sourceName'])
    data_col += ["SOURCE", "STATEMENT_DATE", "System_Idx", "CARRY_FORWARD", "AGEING","DC_AMOUNT", "MATCHING_STATUS", "EXECUTION_STATEMENTDATE"]
    data_col = list(set(data_col))
    if df.empty:
        return {"status": False, "message": "Empty data", "data": []}
    data_col = [each_col for each_col in data_col if each_col in df.columns]
    df = df[df['SOURCE'].isin(source_list)]
    df = df[data_col]
    login_session = await framework.restapi.me()
    userid = login_session.get('given_name')
    downloadpath = os.path.join(framework.settings.mftpath, 'downloads', userid)
    if not os.path.exists(downloadpath):
        os.makedirs(downloadpath)

    # creating link to downloads folder
    ui_path = framework.settings.ui_code_path
    mftpath = framework.settings.mftpath
    if not os.path.exists(f'{ui_path}downloads'):
        os.system(f'ln -s {mftpath}downloads/ {ui_path}')
    df['BULK_FORCEMATCH_COMMENT'] = ''
    df['MATCH GROUP_ID'] = ''
    writer = pandas.ExcelWriter(downloadpath + "/ForceMatchRecords.xlsx")
    df.to_excel(writer, index=False)
    writer.close()
    return {"status": True, "message": "Success","data": os.path.join('/downloads', userid, "ForceMatchRecords.xlsx")}
