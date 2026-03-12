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

@router.post('/template', tags=['CustomReport'])
async def CustomReporttemplate(data: templateParams):
    if not data.stmtdate:
        data1 = reconexecdetailslog_getlatestexedetails.getLatestExeDetailsParams
        data1.reconId = data.reconId
        doc = await reconexecdetailslog_getlatestexedetails.ReconExecDetailsLoggetLatestExeDetails(data1)
        print('doc',doc)
        if doc['status']:
            data.stmtdate = doc["data"][0].get('statementDate', None).strftime('%d-%m-%Y')
        else:
            return {"status": False, "message": "No Latest Execution Found", "data": []}
    
    merge = False
    groupby = False
    sources = []
    dbName = framework.settings.dbName
    ins = framework.elasticmodel.ElasticModel()
    index_statement_date = datetime.datetime.strptime(stmtdate, '%d%m%Y').strftime('%Y-%m-%d')
    index_name = f"{dbName}_reconexecution_{reconId}_{index_statement_date}"
    for each_source, col in data.selected_col[0].__dict__.items():
        sources.append(each_source)
        query = {"query": {"bool": {"must": [{"match": {"SOURCE": each_source}}]}}}
        params = framework.queryparams.QueryParams()
        params.limit = 50000
        params.q = json.dumps(query)
        # try:
        #     each_source + '_df' = await ins.get_all(params, dbName, index_name)
        # except Exception as e:
        #     return {"status": False, "message": e, "data": []}
        # each_source + '_df' = pandas.DataFrame(each_source + '_df'.get('data',[]))
        # each_source + '_df' = each_source + '_df'[col]

    for each_fun in data.order_of_execution:
        if each_fun == 'filter':
            template_df = True
            # for each_source, each_filter in data.filterByObj[0].__dict__.items():
            #     if merge:
            #         merge_df = await filterData(each_filter, merge_df)
            #     else:
            #         each_source + '_df' = await filterData(each_filter, each_source + '_df')

        if each_fun == 'groupby':
            if merge:
                merge_df = await groupBy(data.groupByObj, merge_df)
            # else:
            #     for each_dict in data.groupByObj[0].__dict__:
            #         groupby = True
            #         each_dict['source'] + '_df' = await groupBy(each_dict, each_dict['source'] + '_df')
                    
        if each_fun == 'merge':
            if data.mergeByObj['leftOn']:
                merge = True
                # merge_df = await mergeData(data.mergeByObj.__dict__, data.mergeByObj['leftSource'] + '_df', data.mergeByObj['rightSource'] + '_df')
        
        if merge:
            return {"status": True, "message": "Template Created", "data": merge_df.to_json(orient='records')}
        # else:
        #     data_list = []
        #     return {"status": True, "message": "Template Created", "data": data_list.append(each_source + '_df') for each_source in sources}


async def filterData(each_filter, df):
    for filters in each_filter:
        filters = filters.strip()
        print("Evaluation expression %s" % expression)
        print("BEFORE EXPRESSION:%s" % len(df))
        exec(expression + ';newdf=df')
        df = locals()['newdf']
        print("AFTER EXPRESSION:%s" % len(df))
    return df

async def groupBy(data, df):
    if not data['groupby_columns']:
        return df
    agg_func = {}
    for each_col in data['sum_columns']:
        agg_func[each_col] = np.sum
        df[each_col] = df[each_col].fillna(0)
        df.loc[df[each_col] == '', each_col] = 0
        df[each_col] = df[each_col].astype(np.float64)
    for each_col in data['count_columns']:
        agg_func[each_col] = "count"
    df = df.fillna("")
    df = pandas.pivot_table(
        df,
        index=data['groupby_columns'],
        aggfunc=agg_func
    ).reset_index()
    df.rename(columns=data.rename_columns, inplace=True)
    return df

async def mergeData(data, left, right):
    df = pandas.merge(
        left, right,
        left_on=data['leftOn'], right_on=data['rightOn'],
        how=data['joinType'], suffixes=("", "_" + data['rightSource'])
    )
    return df