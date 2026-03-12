from recons_enum import *
from recons_model import *
import fastapi
import json
import os
import pandas
import zipfile
import numpy as np
import datetime
import reconexecdetailslog_getlatestexedetails\

router = fastapi.APIRouter(prefix='/recons')


@router.post('/uploadForceMatchRecords', tags=['Recons'])

async def ReconsuploadForceMatchRecords(reconId: str, matchrecords: bool,
                                        file: fastapi.UploadFile = fastapi.File(None)):
    data1 = reconexecdetailslog_getlatestexedetails.getLatestExeDetailsParams
    data1.reconId = reconId
    doc = await reconexecdetailslog_getlatestexedetails.ReconExecDetailsLoggetLatestExeDetails(data1)
    if doc['status']:
        stmtdate = doc["data"][0].get('statementDate', None).strftime('%d-%m-%Y')
    else:
        return {"status": False, "message": "No Latest Execution Found", "data": []}

    uploadpath = os.path.join(framework.settings.mftpath, 'forcematch', reconId)
    if not os.path.exists(uploadpath):
        os.makedirs(uploadpath)
    filename = file.filename
    file_contents = await file.read()
    finalfilename = os.path.join(uploadpath, filename)
    with open(finalfilename, "wb") as f:
        f.write(file_contents)

    if finalfilename.endswith('.zip'):
        with zipfile.ZipFile(finalfilename, 'r') as zip_ref:
            zip_ref.extractall(uploadpath)
        os.remove(finalfilename)
    df = pandas.read_excel(finalfilename, dtype='str',engine='openpyxl')
    if 'Reversal' in df['MATCHING_STATUS'].unique().tolist():
        df = df[df['MATCHING_STATUS'] == 'Reversal']
    elif matchrecords:
        df = df[df['MATCHING_STATUS'] == 'UNMATCHED']
    else:
        df = df[df['MATCHING_STATUS'] == 'MATCHED']
    if '' in df['MATCH GROUP_ID'].fillna("").unique().tolist():
        return {"status": False, "message": "Match Group Id missing", "data": []}
    system_idx = df['System_Idx'].unique().tolist()
    dbName = framework.settings.dbName
    ins = framework.postgresmodel.PostgresModel()
    tableName = reconId + "_unmatched"
    query = {"System_Idx": system_idx}
    params = framework.queryparams.QueryParams()
    params.limit = None
    params.q = json.dumps(query)
    try:
        resp = await ins.get_all(params, dbName, tableName)
    except Exception as e:
        print(e)
        return {"status": False, "message": e, "data": []}    
    resp_df = pandas.DataFrame(resp["data"])
    resp_df.to_csv('/tmp/resp_df.csv')
    print("resp_df :", resp_df)
    list_of_column = resp_df.columns.tolist()
    resp_df = resp_df.join(pandas.json_normalize(resp_df['Json Data'])).drop(columns=['Json Data'])
    if "System_Idx" in resp_df:
        resp_df = resp_df.drop_duplicates(subset=["System_Idx"])
    if 'DC_AMOUNT' not in resp_df.columns:
        return {"status": False, "message": "Please change configuration as DC_AMOUNT not avaliable", "data": []}
    resp_df['DC_AMOUNT'] = resp_df['DC_AMOUNT'].fillna(0).astype(np.float64)
    df['DC_AMOUNT'] = df['DC_AMOUNT'].fillna(0).astype(np.float64)
    actual_data = {"success": pandas.DataFrame(), "failed": pandas.DataFrame()}
    print("resp_df -->",resp_df)
    print("df -->",df)
    for each_source in df['SOURCE'].unique().tolist():
        if len(df[df['SOURCE'] == each_source]) != len(resp_df[resp_df['SOURCE'] == each_source]):
            return {"status": False, "message": "Not all records found in database", "data": []}
    login_session = await framework.restapi.me()
    resp_df['BULK_FORCEMATCH_UPDATEDBY'] = login_session.get('email', '')
    resp_df['BULK_FORCEMATCH_UPDATEDDATE'] = datetime.datetime.now().strftime('%d-%m-%Y')
    del resp_df['MATCHING_STATUS']
    if 'BULK_FORCEMATCH_COMMENT' in resp_df.columns:
        del resp_df['BULK_FORCEMATCH_COMMENT']
    if 'MATCH GROUP_ID' in resp_df.columns:
        del resp_df['MATCH GROUP_ID']
    resp_df = resp_df.merge(
        df[['System_Idx', 'MATCHING_STATUS', 'BULK_FORCEMATCH_COMMENT', 'MATCH GROUP_ID']],
        on='System_Idx', suffixes=("", "_y")
    )

    final_df = resp_df.groupby(['SOURCE', 'MATCH GROUP_ID'])[['DC_AMOUNT']].sum().reset_index()
    final_df['compressed'] = final_df['MATCH GROUP_ID']
    resp_df['compressed'] = resp_df['MATCH GROUP_ID']
    payload = {}
    for source in resp_df['SOURCE'].unique().tolist():
        payload[source] = resp_df[resp_df['SOURCE'] == source]
    if 'Reversal' not in df['MATCHING_STATUS'].unique().tolist():
        for grpid in resp_df['compressed'].unique().tolist():
            count = 0
            amount = 0
            for key, data in payload.items():
                if count == 0:
                    amount = data[data['compressed'].isin([grpid])]['DC_AMOUNT'].sum()
                    amount = round(amount)
                data = data[data['compressed'].isin([grpid])]
                if data.empty or amount == 0 or amount != round(data['DC_AMOUNT'].sum()):
                    count = count
                else:
                    count += 1
            if count == len(payload):
                # actual_data['success'] = actual_data['success'].append(resp_df[resp_df['compressed'].isin([grpid])])
                actual_data['success'] = pandas.concat([actual_data['success'],resp_df[resp_df['compressed'].isin([grpid])]])
            else:
                # actual_data['failed'] = actual_data['failed'].append(resp_df[resp_df['compressed'].isin([grpid])])
                actual_data['failed'] = pandas.concat([actual_data['failed'], resp_df[resp_df['compressed'].isin([grpid])]])
    elif not df.empty:
        for self_source in df['SOURCE'].unique().tolist():
            for group_id in resp_df['compressed'].unique().tolist():
                df_Cr = df[
                    (df['SOURCE'] == self_source) & (df['MATCH GROUP_ID'] == group_id) & (df['Dr/Cr Ind'] == 'Cr')]
                df_Dr = df[
                    (df['SOURCE'] == self_source) & (df['MATCH GROUP_ID'] == group_id) & (df['Dr/Cr Ind'] == 'Dr')]
                df_Cr['DC_AMOUNT'] = df_Cr['DC_AMOUNT'].astype(np.float64)
                df_Dr['DC_AMOUNT'] = df_Dr['DC_AMOUNT'].astype(np.float64)
                amount_Dr = df_Dr[df_Dr['SOURCE'] == self_source]['DC_AMOUNT'].sum()
                amount_Cr = df_Cr[df_Cr['SOURCE'] == self_source]['DC_AMOUNT'].sum()
                if amount_Cr == amount_Dr:
                    actual_data['success'] = actual_data['success'].append(
                        resp_df[resp_df['compressed'].isin([group_id])])
                else:
                    actual_data['failed'] = actual_data['failed'].append(
                        resp_df[resp_df['compressed'].isin([group_id])])

    print('*************DATA RETURNED**********')
    for key, data in actual_data.items():
        actual_data[key] = actual_data[key].to_json(orient='records')
    return {"status": True, "message": "Success", "data": actual_data, "matchrecords": matchrecords}
