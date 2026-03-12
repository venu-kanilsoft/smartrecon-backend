import framework.postgresmodel
import framework.queryparams
import framework.types
from recons_enum import *
from recons_model import *
import fastapi
import uuid
import numpy as np
import json
import pandas
import duckdb
import datetime
import jsonpickle
import redis_queue
import ReconExecDetailsLog_stdapi
import SourceReference_stdapi
import recons_stdapi
from sqlalchemy.sql import insert
import sqlalchemy as sqlalk
from typing import List
from sqlalchemy import create_engine, MetaData, Table, select, distinct
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker

router = fastapi.APIRouter()




@router.post('/recons', response_model=Recons, tags=['Recons'])
async def create(inputObj: ReconsCreate):
    
    return await inputObj.create()





@router.put('/recons', response_model=Recons, tags=['Recons'])
async def update(inputObj: Recons):
    
    
    return await inputObj.update()


@router.get('/recons/{id}', response_model=Recons, tags=['Recons'])
async def get(id: str):
    return await Recons.get(id)



@router.get('/recons', response_model=ReconsGetResp, tags=['Recons'])
async def get_all(response: fastapi.Response, params = fastapi.Depends(framework.queryparams.QueryParams)):
    if params.download:
        response.headers['Content-Disposition'] = f'attachment; filename="recons.html"'
    resp = await Recons.get_all(params)
    resp['data'] = sorted(resp['data'], key=lambda x: x['reconProcess']) #Updated Shrihari
    print('resp -->',resp)
    return resp
    #return await Recons.get_all(params) # Commented Shrihari


@router.delete('/recons/{id}', tags=['Recons'])
async def delete(id: str):
    return await Recons.delete(id)


async def _check_recon_status(reconId: str):
    recon_exec_ins = ReconExecDetailsLog_stdapi.ReconExecDetailsLog()
    dbName = framework.settings.dbName
    query = {"reconId": reconId, "jobStatus": "Running"}
    params = framework.queryparams.QueryParams()
    params.limit = 1
    params.fields = None
    params.skip = 0
    params.sort = json.dumps({"statementDate": -1})
    params.q = json.dumps(query)
    resp = await recon_exec_ins.get_all(params, dbName)
    doc = resp.get("data", [])
    if doc:
        return {"status": False, "message":"Recon is running please try after some time", "data": []}
    query = {"reconId": reconId, "jobStatus": "Success"}
    params = framework.queryparams.QueryParams()
    params.limit = 1
    params.fields = None
    params.skip = 0
    params.sort = json.dumps({"statementDate": -1})
    params.q = json.dumps(query)
    resp = await recon_exec_ins.get_all(params, dbName)
    doc = resp.get("data", [])
    if doc:
        stmtdate = doc[0].get('statementDate', None).strftime('%d%m%Y')
        return {"status": True, "message": "Success", "data": stmtdate}
    else:
        return {"status": False, "message": "No LatestExecutions", "data": []}

async def _recomputereconsummary(recon_id: str, stmtdate: str, cyclewise=''):
    dbName = framework.settings.dbName
    ins = framework.postgresmodel.PostgresModel()
    tableName = f"{recon_id}"
    tableName = "recon_summary"
    resp = await _get_data(recon_id, stmtdate, "recon_summary", cyclewise=cyclewise, fields=['_id'])
    #print("*"*100)
    #print(resp)
    if not resp['status']:
        return {"status": False, "message": resp['message'], "data": []}
    list_of_id = [k for d in resp.get("data", []) for k in d.values()]
    listOfRecords = []
    #print(list_of_id)
    recon_sum_path = os.path.join(framework.settings.mftpath, "OUTPUT", recon_id, stmtdate, "recon_summary.csv")
    recon_summary_df = pandas.read_csv(recon_sum_path)
    for eachId in list_of_id:
        summary_df = await getRecords(eachId, "recon_summary")
        print(summary_df)
        #source = summary_df['Json Data']['Source']
        source = summary_df['Source']
        #print(source)
        #summary_df['Json Data']['Auth Waiting'] = 0
        #summary_df['Json Data']['Rollback Waiting'] = 0
        summary_df['Auth Waiting'] = 0
        summary_df['Rollback Waiting'] = 0
        # Self Match
        resp = await _get_data(recon_id, stmtdate, "selfmatched", source=source, cyclewise=cyclewise,
                               fields=['CARRY_FORWARD'])
        resp = pandas.DataFrame(resp.get("data", []))
        if not 'CARRY_FORWARD' in resp.columns:
            resp['CARRY_FORWARD'] = 'N'
        #summary_df['Json Data']['Reversal Count'] = len(resp)
        #summary_df['Json Data']['Carry-Forward Reversal Count'] = len(resp[resp['CARRY_FORWARD'] == 'Y'])
        summary_df['Reversal Count'] = len(resp)
        summary_df['Carry-Forward Reversal Count'] = len(resp[resp['CARRY_FORWARD'] == 'Y'])
        recon_summary_df.loc[recon_summary_df['Source'] == source, "Reversal Count"] = len(resp)

        resp = await _get_data(recon_id, stmtdate, "matched", source=source, cyclewise=cyclewise,
                               fields=['CARRY_FORWARD'])
        resp = pandas.DataFrame(resp.get("data", []))
        if not 'CARRY_FORWARD' in resp.columns:
            resp['CARRY_FORWARD'] = 'N'
        #summary_df['Json Data']['Matched Count'] = len(resp[resp['CARRY_FORWARD'] == 'N'])
        #summary_df['Json Data']['Carry-Forward Matched Count'] = len(resp[resp['CARRY_FORWARD'] == 'Y'])
        summary_df['Matched Count'] = len(resp[resp['CARRY_FORWARD'] == 'N'])
        summary_df['Carry-Forward Matched Count'] = len(resp[resp['CARRY_FORWARD'] == 'Y'])
        recon_summary_df.loc[recon_summary_df['Source'] == source, "Matched Count"] = len(resp[resp['CARRY_FORWARD'] == 'N'])
        recon_summary_df.loc[recon_summary_df['Source'] == source, "Carry-Forward Matched Count"] = len(resp[resp['CARRY_FORWARD'] == 'Y'])

        resp = await _get_data(recon_id, stmtdate, "unmatched", source=source, cyclewise=cyclewise,
                               fields=['CARRY_FORWARD'])
        #print(resp)
        resp = pandas.DataFrame(resp.get("data", []))
        #print(resp)
        if not 'CARRY_FORWARD' in resp.columns:
            resp['CARRY_FORWARD'] = 'N'
        #summary_df['Json Data']['UnMatched Count'] = len(resp[resp['CARRY_FORWARD'] == 'N'])
        #summary_df['Json Data']['Carry-Forward UnMatched Count'] = len(resp[resp['CARRY_FORWARD'] == 'Y'])
        summary_df['UnMatched Count'] = len(resp[resp['CARRY_FORWARD'] == 'N'])
        summary_df['Carry-Forward UnMatched Count'] = len(resp[resp['CARRY_FORWARD'] == 'Y'])
        recon_summary_df.loc[recon_summary_df['Source'] == source, "UnMatched Count"] = len(resp[resp['CARRY_FORWARD'] == 'N'])
        recon_summary_df.loc[recon_summary_df['Source'] == source, "Carry-Forward UnMatched Count"] = len(resp[resp['CARRY_FORWARD'] == 'Y'])

        # Auth Waiting Count
        # query = {"family": "authwaiting", "SOURCE": source, "EXECUTION_STATEMENTDATE": datetime.datetime.strptime(stmtdate, '%d%m%Y').isoformat()}
        # count = await ins.get_count(query, [], dbName, tableName)
        resp = await _get_data(recon_id, stmtdate, "authwaiting", source=source, cyclewise=cyclewise,
                               fields=['CARRY_FORWARD'])
        resp = pandas.DataFrame(resp.get("data", []))
        #summary_df['Json Data']['Auth Waiting'] = len(resp)
        summary_df['Auth Waiting'] = len(resp)
        recon_summary_df.loc[recon_summary_df['Source'] == source, "Auth Waiting"] = len(resp)

        # Rollback Count
        # query = {"family": "rollbackwaiting", "SOURCE": source, "EXECUTION_STATEMENTDATE": datetime.datetime.strptime(stmtdate, '%d%m%Y').isoformat()}
        # count = await ins.get_count(query, [], dbName, tableName)
        resp = await _get_data(recon_id, stmtdate, "rollbackwaiting", source=source, cyclewise=cyclewise,
                               fields=['CARRY_FORWARD'])
        resp = pandas.DataFrame(resp.get("data", []))
        #summary_df['Json Data']['Rollback Waiting'] = len(resp)
        summary_df['Rollback Waiting'] = len(resp)
        recon_summary_df.loc[recon_summary_df['Source'] == source, "Rollback Waiting"] = len(resp)
        recon_summary_df.to_csv(recon_sum_path, index=False)
        listOfRecords.append(summary_df)
    resp = await updateRecords(listOfRecords, tableName)
    #await updateConsolidate(recon_id, stmtdate)

    # GL Summary update
    resp = await _get_data(recon_id, stmtdate, "gl_recon_summary", cyclewise=cyclewise, fields=['_id'])
    if not resp['status']:
        return {"status": False, "message": resp['message'], "data": []}
    list_of_id = [k for d in resp.get("data", []) for k in d.values()]
    listOfRecords = []
    for eachId in list_of_id:
        summary_df = await getRecords(eachId, "recon_summary")
        print("summary_df: ", summary_df)
        # source = summary_df['Json Data']['Source']
        source = summary_df['Source']
        print(source)
        gl_number = summary_df['GL_NUMBER']
        # summary_df['Json Data']['Auth Waiting'] = 0
        # summary_df['Json Data']['Rollback Waiting'] = 0
        
        summary_df['Auth Waiting'] = 0
        summary_df['Rollback Waiting'] = 0
        resp = await _get_data(recon_id, stmtdate, "matched", source=source, cyclewise=cyclewise,
                               gl_number=gl_number, fields=['CARRY_FORWARD'])
        resp = pandas.DataFrame(resp.get("data", []))
        if not 'CARRY_FORWARD' in resp.columns:
            resp['CARRY_FORWARD'] = 'N'
        # summary_df['Json Data']['Matched Count'] = len(resp[resp['CARRY_FORWARD'] == 'N'])
        # summary_df['Json Data']['Carry-Forward Matched Count'] = len(resp[resp['CARRY_FORWARD'] == 'Y'])
        
        summary_df['Matched Count'] = len(resp[resp['CARRY_FORWARD'] == 'N'])
        summary_df['Carry-Forward Matched Count'] = len(resp[resp['CARRY_FORWARD'] == 'Y'])

        resp = await _get_data(recon_id, stmtdate, "unmatched", source=source, cyclewise=cyclewise,
                               gl_number=gl_number, fields=['CARRY_FORWARD'])
        print(resp)
        resp = pandas.DataFrame(resp.get("data", []))
        if not 'CARRY_FORWARD' in resp.columns:
            resp['CARRY_FORWARD'] = 'N'
        # summary_df['Json Data']['UnMatched Count'] = len(resp[resp['CARRY_FORWARD'] == 'N'])
        # summary_df['Json Data']['Carry-Forward UnMatched Count'] = len(resp[resp['CARRY_FORWARD'] == 'Y'])
        
        summary_df['UnMatched Count'] = len(resp[resp['CARRY_FORWARD'] == 'N'])
        summary_df['Carry-Forward UnMatched Count'] = len(resp[resp['CARRY_FORWARD'] == 'Y'])

        # Auth Waiting Count
        # query = {"family": "authwaiting", "SOURCE": source, "GL_NUMBER": gl_number, "EXECUTION_STATEMENTDATE": datetime.datetime.strptime(stmtdate, '%d%m%Y').isoformat()}
        # count = await ins.get_count(query, [], dbName, tableName)
        resp = await _get_data(recon_id, stmtdate, "authwaiting", source=source, cyclewise=cyclewise, gl_number=gl_number,
                               fields=['CARRY_FORWARD'])
        resp = pandas.DataFrame(resp.get("data", []))
        summary_df['Json Data']['Auth Waiting'] = len(resp)

        # Rollback Count
        # query = {"family": "rollbackwaiting", "SOURCE": source, "GL_NUMBER": gl_number, "EXECUTION_STATEMENTDATE": datetime.datetime.strptime(stmtdate, '%d%m%Y').isoformat()}
        # count = await ins.get_count(query, [], dbName, tableName)
        resp = await _get_data(recon_id, stmtdate, "rollbackwaiting", source=source, cyclewise=cyclewise,
                               gl_number=gl_number, fields=['CARRY_FORWARD'])
        resp = pandas.DataFrame(resp.get("data", []))
        # summary_df['Json Data']['Rollback Waiting'] = len(resp)
        summary_df['Rollback Waiting'] = len(resp)
        listOfRecords.append(summary_df)
    resp = await updateRecords(listOfRecords, tableName)

    return {"status": True, "message": "Success", "data": []}

async def _get_data(reconId: str, stmtdate: str, operation: str, source='', cyclewise='', gl_number='', fields=None):
    dbName = framework.settings.dbName
    recon_exec_ins = ReconExecDetailsLog_stdapi.ReconExecDetailsLog()
    dbName = framework.settings.dbName
    query = {"reconId": reconId, "jobStatus": "Success"}
    params = framework.queryparams.QueryParams()
    params.limit = 1
    params.fields = None
    params.skip = 0
    params.sort = json.dumps({"statementDate": -1})
    params.q = json.dumps(query)
    resp = await recon_exec_ins.get_all(params, dbName)
    latest_date = resp['data'][0].get("statementDate").strftime("%d%m%Y")

    ins = framework.postgresmodel.PostgresModel()
    tableName = f"{reconId}"
    if operation in ['matched', 'rollbackwaiting', 'selfmatched']:
        tableName = f'{reconId}_matched'
    if operation in ['unmatched', 'authwaiting']:
        tableName = f'{reconId}_unmatched'
    if operation in ['recon_summary', 'gl_recon_summary']:
        tableName = "recon_summary"
    query = {"RECON_ID": reconId, "species": operation, "EXECUTION_STATEMENTDATE": datetime.datetime.strptime(stmtdate, '%d%m%Y').isoformat()}
    if source:
        query['SOURCE'] = source
    if gl_number:
        query['GL_NUMBER'] = gl_number
    if cyclewise:
        query['EXECUTION_CYCLE'] = cyclewise
        if operation == 'recon_summary':
            query['species'] = str(operation) + '_' + str('cyclewise')
    params = framework.queryparams.QueryParams()
    params.limit = None
    if operation in ["authwaiting", "rollbackwaiting"] and str(latest_date) != str(stmtdate):
        params.limit = 0
    params.fields = fields
    params.q = json.dumps(query)
    #print(query)
    try:
        resp = await ins.get_all(params, dbName, tableName)
        return {"status": True, "message": "Success", "data": resp.get("data", []),
                "old_scroll_id": resp.get("old_scroll_id", "")}
    except Exception as e:
        return {"status": True, "message": e, "data": []}

async def _netSplit(recon_id: str, stmtdate: str, records: str, sources: str, linkids: str):
    login_session = await framework.restapi.me()
    email = login_session.get('email', '')
    final_net_split_df = pandas.DataFrame()
    net_dataframe = pandas.DataFrame(records)
    sourceOne = net_dataframe[net_dataframe['SOURCE'] == sources[0]]
    sourceTwo = net_dataframe[net_dataframe['SOURCE'] == sources[1]]
    print(sourceOne)
    print(sourceTwo)
    print('linkids', linkids)
    sourceOne['DC_AMOUNT'] = sourceOne['DC_AMOUNT'].astype(np.float64)
    sourceTwo['DC_AMOUNT'] = sourceTwo['DC_AMOUNT'].astype(np.float64)
    for linkid in linkids:
        sourceOneData = sourceOne[sourceOne['LINK_ID'] == str(linkid)]
        sourceTwoData = sourceTwo[sourceTwo['LINK_ID'] == str(linkid)]
        print(sourceOneData['DC_AMOUNT'])
        print(sourceTwoData['DC_AMOUNT'])
        if sourceOneData['DC_AMOUNT'].sum() > sourceTwoData['DC_AMOUNT'].sum():
            print('came into if condition')
            sourceOneData = sourceOneData.reset_index(drop=True)
            net_split_df = sourceOneData.iloc[[0]]
            net_split_df['DC_AMOUNT'] = [abs(sourceOneData['DC_AMOUNT'].sum()) - abs(sourceTwoData['DC_AMOUNT'].sum())]
            net_split_df['NET SPLIT LINK_ID'] =[ linkid]
            net_split_df['LINK_ID'] = [str(uuid.uuid4().hex)]
            net_split_df['NET SPLIT UPDATED_BY'] = [email]
            net_split_df['NET SPLIT UPDATED DATE'] = [datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')]
            final_net_split_df = final_net_split_df.append(net_split_df, ignore_index=True)
        elif sourceTwoData['DC_AMOUNT'].sum() > sourceOneData['DC_AMOUNT'].sum():
            print('came into el if condition')
            net_split_df = sourceTwoData.iloc[[0]]
            sourceOneData = sourceOneData.reset_index(drop=True)
            net_split_df['DC_AMOUNT'] = [abs(sourceTwoData['DC_AMOUNT'].sum()) - abs(sourceOneData['DC_AMOUNT'].sum())]
            net_split_df['NET SPLIT LINK_ID'] = [linkid]
            net_split_df['LINK_ID'] = [str(uuid.uuid4().hex)]
            net_split_df['NET SPLIT UPDATED_BY'] = [email]
            net_split_df['NET SPLIT UPDATED DATE'] = [datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')]
            final_net_split_df = final_net_split_df.append(net_split_df, ignore_index=True)
    print(net_split_df)
    return True, final_net_split_df

async def add_key(data: str) -> dict:
    data["madeby"] = "Bae systems"
    return data

async def customReport(reconId, stmtdate):
    sourceList = []
    login_session = await framework.restapi.me()
    createdBy = login_session.get('email', '')
    
    # fetch recon data
    recons_ins = Recons()
    recondata = await recons_ins.get(reconId, framework.settings.dbName)
    recondata = recondata
    
    reconsources = recondata.get('sources', [])
    reconName = recondata.get('reconName', '')
    reconProcess = recondata.get('reconProcess', '')
    if not reconsources:
        return False, "Sources are not configured."
    
    source_ref_ins = SourceReference_stdapi.SourceReference()
    sourceIdNameMap = {}
    for src in reconsources:
        # finding the source reference of this source
        sourceref = await source_ref_ins.get(src, framework.settings.dbName)
        sourceref = sourceref
        if not sourceref:
            continue
        sourceList.append(sourceref.get('source', ''))
        sourceIdNameMap[src] = sourceref.get('source', '')
    
    doc = {
        'sourceIdNameMap':sourceIdNameMap, 'reconProcess':reconProcess, 'reconId':reconId,
        'sourceName':sourceList,'stmtdate': stmtdate,
        'reconName':reconName, "createdBy": createdBy, 'op': "customreport"
    }
    await redis_queue._RedisQueue('assetProcessor').put(jsonpickle.dumps({"tenant": framework.ctx['tenant'], "data": doc}))
    return True, "Reports are regenerating in background"

# df['col1'] = df['col1'].apply(lambda x: add_key(x))

async def getRecords(id: str, tableName: str):
    conn_string = framework.settings.db_urls["postgres"][0]
    engine = create_engine(conn_string)
    metadata = MetaData(bind=engine)
    connection = engine.connect()
    tableSchema = Table(tableName, metadata, autoload=True)
    select_query = select([tableSchema]).where(tableSchema.c._id == id)
    respProxy = connection.execute(select_query)
    resp = respProxy.fetchall()
    row_as_dict = {}
    for row in resp:
        # row_as_dict = row._mapping # SQLAlchemy 1.4 and greater
        row_as_dict = dict(row) # SQLAlchemy 1.3 and earlier
    connection.close()
    engine.dispose()
    return row_as_dict

async def updateRecords(record: List[dict], tableName: str):
    conn_string = framework.settings.db_urls["postgres"][0]
    engine = create_engine(conn_string)
    metadata = MetaData(bind=engine)
    connection = engine.connect()
    try:
        tableSchema = Table(tableName, metadata, autoload=True)
        for eachRecord in record:
            query = sqlalk.update(tableSchema).values(**eachRecord)
            query = query.where(tableSchema.columns._id == eachRecord['_id'])
            connection.execute(query)
        # connection.commit()
        connection.close()
        engine.dispose()
        return record
    except SQLAlchemyError as e:
        # Rollback the transaction if any update fails
        # connection.rollback()
        print("Update failed. Rolling back all changes.")
        print(e)
        raise ValueError(e)

async def getBulkRecords(id: List[str], tableName: str):
    conn_string = framework.settings.db_urls["postgres"][0]
    engine = create_engine(conn_string)
    metadata = MetaData(bind=engine)
    connection = engine.connect()
    tableSchema = Table(tableName, metadata, autoload=True)
    chunk_size = 10000
    chunks = [id[i:i + chunk_size] for i in range(0, len(id), chunk_size)]
    dataframes=[]
    for chunk in chunks:
        select_query = select([tableSchema]).where(tableSchema.c._id.in_(chunk))
        respProxy = connection.execute(select_query)
        rows = respProxy.fetchall()
        cols = respProxy.keys()
        temp = pandas.DataFrame([dict(zip(cols, row)) for row in rows])
        dataframes.append(temp)
    df = pandas.concat(dataframes, ignore_index=True)
    connection.close()
    engine.dispose()
    print(df)
    return df

async def deleteRecords(record_ids: List[str], tableName: str):
    try:
        conn_string = framework.settings.db_urls["postgres"][0]
        engine = create_engine(conn_string)
        metadata = MetaData(bind=engine)
        Session = sessionmaker(bind=engine)
        session = Session()
        tableSchema = sqlalk.Table(tableName, metadata, autoload=True, autoload_with=engine)
        #### SQLAlchemy 1.3 and earlier ####
        deleted_objects = session.query(tableSchema).filter(tableSchema.c._id.in_(record_ids))
        deleted_objects.delete(synchronize_session=False)
        session.commit()
        if session:
            session.close()
        engine.dispose()
    except SQLAlchemyError as e:
        print("Update failed. Rolling back all changes.")
        print(e)
        return {}

async def insertRecords_bkp(records: List[dict], tableName: str):
    try:
        conn_string = framework.settings.db_urls["postgres"][0]
        engine = create_engine(conn_string)
        metadata = MetaData(bind=engine)
        Session = sessionmaker(bind=engine)
        session = Session()
        tableSchema = sqlalk.Table(tableName, metadata, autoload=True, autoload_with=engine)
        session.bulk_insert_mappings(tableSchema, records)
        session.commit()
    except Exception as e:
        # Rollback the transaction in case of an error
        session.rollback()
        print(e)
        return {}
    finally:
        # Close the session
        session.close()

async def insertRecords(records: List[dict], tableName: str):
    # try:
    conn_string = framework.settings.db_urls["postgres"][0]
    engine = create_engine(conn_string)
    metadata = MetaData(bind=engine)
    metadata.reflect(bind=engine)
    connection = engine.connect()
    tableSchema = Table(tableName, metadata, autoload=True, autoload_with=engine)
    connection.execute(insert(tableSchema), records)
    connection.close()
    # except Exception as e:
    #     # Rollback the transaction in case of an error
    #     print(e)
    #     return {}
    # finally:
    #     # Close the session
    #     connection.close()


async def getDistinctValue(query: dict, tableName: str, distinctColumn: str):
    conn_string = framework.settings.db_urls["postgres"][0]
    engine = create_engine(conn_string)
    metadata = MetaData(bind=engine)
    connection = engine.connect()
    tableSchema = Table(tableName, metadata, autoload=True)
    innerQuery = []
    for key, val in query.items():
        if not isinstance(val, list):
            val = [val]
        innerQuery.append(tableSchema.c[key].in_(val))

    query = tableSchema.select().with_only_columns([distinct(tableSchema.c[distinctColumn])]).where(
        sqlalk.and_(*innerQuery))
    results = connection.execute(query)
    distinct_values = results.fetchall()
    distinct_values = [''.join(i) for i in distinct_values]
    connection.close()
    engine.dispose()
    return distinct_values

async def updateConsolidate(reconId: str, stmtdate: str):
    outputPath = os.path.join(framework.settings.mftpath, "OUTPUT", reconId, stmtdate)
    query = {"reconId": reconId}
    params = framework.queryparams.QueryParams()
    params.limit = 100
    params.skip = 0
    params.q = json.dumps(query)
    sourceins = SourceReference_stdapi.SourceReference()
    reconsins = recons_stdapi.Recons()
    recons_resp = await reconsins.get(reconId)
    if not isinstance(recons_resp, dict):
        recons_resp = recons_resp.__dict__
    reconName = recons_resp.get("reconName")
    resp = await sourceins.get_all(params, framework.settings.dbName)
    resp = resp.get('data', [])
    sourceName = []
    for each_source_ref in resp:
        #print(each_source_ref)
        sourceName.append(each_source_ref['source'])
    #print(sourceName)
    recon_summary = pandas.read_csv(os.path.join(outputPath, 'recon_summary.csv'), dtype=str)
    writer = pandas.ExcelWriter(outputPath + "/ConsolidatedReport.xlsx", engine="xlsxwriter")
    for  each_source in sourceName:
        all_data = pandas.DataFrame()
        if os.path.exists(os.path.join(outputPath, each_source + '.csv')):
            match_df = pandas.read_csv(os.path.join(outputPath, each_source + '.csv'), dtype=str)
            all_data = all_data.append(match_df)
            if "DC_AMOUNT" in match_df.columns:
                match_df["DC_AMOUNT"] = match_df["DC_AMOUNT"].astype(np.float64)
                if not "CARRY_FORWARD" in match_df.columns:
                    match_df['CARRY_FORWARD'] = "N"
                match_amt = match_df[match_df['CARRY_FORWARD'] == "N"]["DC_AMOUNT"].sum()
                cf_match_amt = match_df[match_df['CARRY_FORWARD'] == "Y"]["DC_AMOUNT"].sum()
                recon_summary.loc[recon_summary["Source"] == each_source, "Matched Amount"] = match_amt
                recon_summary.loc[recon_summary["Source"] == each_source, "Carry-Forward Matched Amount"] = cf_match_amt
            del match_df
        if os.path.exists(os.path.join(outputPath, each_source + '_UnMatched.csv')):
            un_match_df = pandas.read_csv(os.path.join(outputPath, each_source + '_UnMatched.csv'), dtype=str)
            all_data = all_data.append(un_match_df)
            if "DC_AMOUNT" in un_match_df.columns:
                if not "CARRY_FORWARD" in un_match_df.columns:
                    un_match_df['CARRY_FORWARD'] = "N"
                un_match_df["DC_AMOUNT"] = un_match_df["DC_AMOUNT"].astype(np.float64)
                un_match_amt = un_match_df[un_match_df['CARRY_FORWARD'] == "N"]["DC_AMOUNT"].sum()
                cf_un_match_amt = un_match_df[un_match_df['CARRY_FORWARD'] == "Y"]["DC_AMOUNT"].sum()
                recon_summary.loc[recon_summary["Source"] == each_source, "UnMatched Amount"] = un_match_amt
                recon_summary.loc[recon_summary["Source"] == each_source, "Carry-Forward UnMatched Amount"] = cf_un_match_amt
            del un_match_df
        all_data = all_data.reset_index(drop=True)
        all_data.to_excel(writer, sheet_name=each_source, index=False)
        if os.path.exists(os.path.join(outputPath, each_source + '_Filtered.csv')):
            filter_df = pandas.read_csv(os.path.join(outputPath, each_source + '_Filtered.csv'), dtype=str)
            filter_df.to_excel(writer, sheet_name=each_source + '_Filtered', index=False)
    recon_summary.to_csv(os.path.join(outputPath, 'recon_summary.csv'), index=False)
    if os.path.exists(os.path.join(outputPath, 'recon_summary.csv')):
        recon_summary = pandas.read_csv(os.path.join(outputPath, 'recon_summary.csv'), dtype=str)
        recon_summary.to_excel(writer, sheet_name=f'{reconName} Summary', index=False)
    writer.save()

async def _get_data_duckdb_bkp(reconId: str, stmtdate: str, operation: str, source=None, limit=500000, offset=0):
    conn = duckdb.connect(database=':memory:')
    exec_date = datetime.datetime.strptime(stmtdate, "%d%m%Y")
    year, month, day = exec_date.year, exec_date.month, exec_date.day
    where_cond = f"year = {year} and month = {month} and day = {day}"
    data = pandas.DataFrame()
    if source:
        for each_source in source:
            # if isinstance(source, list):
            #     source = tuple(source)
            #     # source = 'ALP_TRANSACTION_DETAILS'
            where_cond += f" and SOURCE = '{each_source}'"
            where_cond += f" and species = '{operation}'"
            query = f"select * from read_parquet('{framework.settings.mftpath}duckdb/{reconId}/*/*/*/*/*/*.parquet'," \
                    f"hive_partitioning=True, union_by_name=True) where {where_cond};"# limit {limit} offset {offset};" # binary_as_string=True
            count_query = f"select count(*) from read_parquet('{framework.settings.mftpath}duckdb/{reconId}/*/*/*/*/*/*.parquet'," \
                    f"hive_partitioning=True, union_by_name=True) where {where_cond};"
        print(query)
        source_data = conn.execute(query).fetchdf()
        print(source_data)
        print(source_data.columns)
        source_data = source_data.fillna("")
        toatal_count = conn.execute(count_query).fetchdf()['count_star()'][0]
        conn.close()
        print(len(source_data))
        if len(source_data) < limit:
            pagination = False
        else:
            pagination = True
        print(source_data['species'].unique().tolist())
        source_data = source_data[source_data['species'] == operation]
        group_by_list = ['year', 'month', 'day', 'SOURCE', 'species']
        col_rename = {col: "_".join(col.split("_")[:-1]) for i, col in enumerate(source_data.columns) if col not in group_by_list}
        source_data.rename(columns=col_rename, inplace=True)
        data = data.append(source_data)
    print(toatal_count)
    print(data.columns.tolist())
    print(len(data))
    # print(round(len(data)/toatal_count * 100, 2))
    return {
        "status": True, 
        "message": "Success", 
        "data": data, 
        "toatal_count": toatal_count,
        "columns": data.columns.tolist(),
        "percentage": 0
    }


async def _get_data_duckdb(reconId: str, stmtdate: str, operation: str, source=None, limit=50000, offset=0):
    conn = duckdb.connect()
    exec_date = datetime.datetime.strptime(stmtdate, "%d%m%Y")
    year, month, day = exec_date.year, exec_date.month, exec_date.day
    where_cond = f"year = {year} and month = {month} and day = {day}"
    if source:
        print(source)
        # for each_source in source:
        #     where_cond += f" and SOURCE = {each_source}"
        # where_cond += f" and species = {operation};"
    query = f"select * from read_parquet('{framework.settings.mftpath}duckdb/{reconId}/*/*/*/*/*/*.parquet'," \
            f"hive_partitioning=True, union_by_name=True) where {where_cond} limit {limit};"# limit {limit} offset {offset};"
    count_query = f"select count(*) from read_parquet('{framework.settings.mftpath}duckdb/{reconId}/*/*/*/*/*/*.parquet'," \
            f"hive_partitioning=True, union_by_name=True) where {where_cond};"
    print(query)
    data = conn.execute(query).fetchdf()
    # toatal_count = conn.execute(count_query).fetchdf()['count_star()'][0]
    toatal_count = 1
    print(len(data))
    if len(data) < limit:
        pagination = False
    else:
        pagination = True
    print(data['species'].unique().tolist())
    group_by_list = ['year', 'month', 'day', 'SOURCE', 'species']
    col_rename = {col: "_".join(col.split("_")[:-1]) for i, col in enumerate(data.columns) if col not in group_by_list}
    data.rename(columns=col_rename, inplace=True)
    data = data[data['species'] == operation]
    # print(toatal_count)
    # print(data.columns.tolist())
    # print(round(len(data)/toatal_count * 100, 2))
    return {
        "status": True, 
        "message": "Success", 
        "data": data, 
        "toatal_count": toatal_count,
        "columns": data.columns.tolist(),
        "percentage": round(len(data)/toatal_count * 100, 2)
    }
