from CustomReport_enum import *
from CustomReport_model import *
import json
import fastapi
import pandas
import datetime
import numpy as np
import psycopg2
import reconexecdetailslog_getlatestexedetails

router = fastapi.APIRouter(prefix='/customreport')

@router.post('/groupBy', tags=['CustomReport'])
async def CustomReportgroupBy(data: groupByParams):
    dbName = framework.settings.dbName
    if not data.stmtdate:
        data1 = reconexecdetailslog_getlatestexedetails.getLatestExeDetailsParams
        data1.reconId = data.reconId
        doc = await reconexecdetailslog_getlatestexedetails.ReconExecDetailsLoggetLatestExeDetails(data1)
        print('doc',doc)
        if doc['status']:
            data.stmtdate = datetime.datetime.fromisoformat(
                    doc["data"][0].get('statementDate', None)).strftime('%d-%m-%Y')
        else:
            return {"status": False, "message": "No Latest Execution Found", "data": []}
    try:
        conn_string = framework.settings.db_urls["postgres"][0]
        pg_conn = psycopg2.connect(conn_string)
        cur = pg_conn.cursor()
        date = datetime.datetime.strptime(data.stmtdate, "%d-%m-%Y")
        # table_name = reconId + '_' + srcname.lower()
        table_name = data.reconId
        query = f'''SELECT * FROM "{table_name}" WHERE "EXECUTION_STATEMENTDATE" = '{date}' AND "SOURCE" = '{data.source}';'''
        cur.execute(query)
        cols = list(map(lambda x: x[0], cur.description)) 
        unmatched_data = cur.fetchall()
        unmatched_data = pandas.DataFrame(unmatched_data, columns=cols)
        df = pandas.concat([unmatched_data, pandas.DataFrame(unmatched_data['Json Data'])], axis=1)
        if 'Json Data' in df.columns:
            del df['Json Data']
        pg_conn.commit()
        cur.close()
    except Exception as e:
        print(e)
        cur.close()
        df = pandas.DataFrame()
    # df = pandas.DataFrame(reconsummary_data)
    aggfun_col = {}
    rename_col = {}
    # Creating Agg Function dict
    for each_sum in data.sum_columns:
        aggfun_col[each_sum] = np.sum
    for each_count in data.count_columns:
        aggfun_col[each_count] = "count"
    # creating Rename Columns dict
    data.rename_columns = data.rename_columns.__dict__
    print(data.rename_columns)
    for org_col, re_col in zip(data.rename_columns['columns'], data.rename_columns['rename']):
        rename_col[org_col] = re_col
    if not df.empty:
        for each_amt in data.sum_columns:
            df.loc[df[each_amt] == '', each_amt] = 0
            df[each_amt] = df[each_amt].fillna(0).astype(np.float64)
        df = df.fillna("")
        df = pandas.pivot_table(
            df,
            index=data.groupby_columns,
            aggfunc=aggfun_col
        )
        df.rename(columns=rename_col, inplace=True)
    return {"status": True, "message": "Success", "data": df.to_json(orient='records')}