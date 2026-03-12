from CustomReport_enum import *
from CustomReport_model import *
import fastapi
import framework
import datetime
import reconexecdetailslog_getlatestexedetails
import pandas
import json
import jinja2
import psycopg2
import datetime
import CustomReport_stdapi

router = fastapi.APIRouter(prefix='/customreport')

@router.post('/loadReport', tags=['CustomReport'])
async def CustomReportloadReport(data: loadReportParams):
    data1 = reconexecdetailslog_getlatestexedetails.getLatestExeDetailsParams
    data1.reconId = data.reconId
    doc = await reconexecdetailslog_getlatestexedetails.ReconExecDetailsLoggetLatestExeDetails(data1)
    if doc['status']:
        stmtdate = datetime.datetime.fromisoformat(
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
        query = f'''SELECT * FROM "{table_name}" WHERE "EXECUTION_STATEMENTDATE" = '{date}' AND "MATCHING_STATUS" IN ('MATCHED', 'UNMATCHED');'''
        cur.execute(query)
        cols = list(map(lambda x: x[0], cur.description)) 
        unmatched_data = cur.fetchall()
        unmatched_data = pandas.DataFrame(unmatched_data, columns=cols)
        df = pandas.concat([unmatched_data, pandas.DataFrame(unmatched_data['Json Data'])], axis=1)
        if 'Json Data' in df.columns:
            del df['Json Data']
        pg_conn.commit()
        cur.close()
        {"status": True, "message": "Success", "data": df.to_json(orient='records')}
    except Exception as e:
        {"status": False, "message": e, "data": []}
