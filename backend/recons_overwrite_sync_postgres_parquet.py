import asyncpg
import jsonpickle

from recons_enum import *
from recons_model import *
import os
import json
import shutil
import fastapi
import framework
import redis_queue
import polars as pl
import pandas as pd
import pyarrow as pa
import recons_stdapi
import framework.restapi
import pyarrow.parquet as pq
import SourceReference_stdapi

router = fastapi.APIRouter(prefix='/recons')


# @router.post('/overwrite_sync_postgres_parquet', tags=['Recons'])
# async def Reconsoverwrite_sync_postgres_parquet(data: overwrite_sync_postgres_parquetParams):
#     if not data.redis_queue:
#         conn = await asyncpg.connect(
#             user=framework.settings.Postgres_UserName,
#             host=framework.settings.Postgres_Host,
#             port=framework.settings.Postgres_Port,
#             password=framework.settings.Postgres_password,
#             database=framework.settings.databaseName
#         )
#         try:
#             stmt = f'''SELECT * FROM "{data.reconId}" WHERE "EXECUTION_STATEMENTDATE" = '{data.exec_date}';'''
#             print(stmt)
#             async with conn.transaction():
#                 cursor = await conn.cursor(stmt)

#                 while True:
#                     records = await cursor.fetch(1000000)

#                     if not records:
#                         print("In Break")
#                         break

#                     df = [dict(row) for row in records]
#                     df = pl.DataFrame(df)
#                     print(len(df))
#                     df = df.with_columns(
#                         [
#                             pl.col('EXECUTION_STATEMENTDATE').dt.year().alias('year'),
#                             pl.col('EXECUTION_STATEMENTDATE').dt.month().alias('month'),
#                             pl.col('EXECUTION_STATEMENTDATE').dt.day().alias('day'),
#                         ]
#                     )
#                     df = df.with_columns(
#                             pl.when(~pl.col("family").is_in(['matched', 'unmatched', 'dropped', 'failed', 'duplicated', 'selfmatched', 'authwaiting', 'rollbackwaiting', 'gl_recon_summary']))
#                             .then(pl.col("family"))
#                             .otherwise(pl.col("SOURCE"))
#                             .alias("SOURCE")
#                         )
#                     df = df.fill_null("")
#                     df = df.to_pandas()
#                     df = df[df['family'] != 'gl_recon_summary']
#                     df = df[df['family'] != 'recon_summary']
#                     # print(df['Json Data'].unique().tolist())
#                     df['Json Data'] = df['Json Data'].apply(json.loads)
#                     if '__index_level_0_' in df.columns.tolist():
#                         del df['__index_level_0_']
#                     if '__index_level_0__' in df.columns.tolist():
#                         del df['__index_level_0__']
#                     if 'index' in df.columns.tolist():
#                         del df['index']
#                     df = df.reset_index()
#                     df = df.join(pd.json_normalize(df['Json Data'])).drop(columns=['Json Data'])
#                     df.rename(columns={"Source": "SummarySource"}, inplace=True)
#                     df = df.fillna("")
#                     df = df.astype(str)
#                     print(len(df))
#                     print(df.columns.tolist())
#                     # print(df['UPDATED_BY'].unique().tolist())
#                     # print(df['DC_AMOUNT'])
#                     # print(df.columns.tolist())
#                     group_by_list = ['year', 'month', 'day', 'SOURCE', 'species']
#                     col_rename = {col: f"{col}_{''.join(str(ord(c)) for c in col)}" for i, col in enumerate(df.columns) if col not in group_by_list}
#                     df.rename(columns=col_rename, inplace=True)
#                     print(df.columns.tolist())
#                     partitions = df.groupby(group_by_list)
#                     # partitions = df.groupby(['year', 'month', 'day', 'SOURCE', 'species'])
#                     for partition, sample_df in partitions:
#                         print("partitions: ",partition)
#                         print("df columns: ", sample_df.columns)
#                         print(len(sample_df))
#                         partition_path = f'{framework.settings.mftpath}/duckdb/{data.reconId}/'
#                         table = pa.Table.from_pandas(sample_df)
#                         pq.write_to_dataset(
#                             table,
#                             root_path=partition_path,
#                             existing_data_behavior='delete_matching',
#                             partition_cols=group_by_list
#                         )

#         finally:
#             await conn.close()

#         return {
#             "status": True, "message": "Sync Completed", "data": []
#         }

#     else:
#         await redis_queue._RedisQueue('assetProcessor').put(
#             jsonpickle.dumps({"op":"Overwrite_Sync_Postgres_Parquet", "data": {"reconId": data.reconId, "exec_date": data.exec_date}}))
#         return {
#             "status": True, "message": "Sync Started.", "data": []
#         }


@router.post('/overwrite_sync_postgres_parquet', tags=['Recons'])
async def Reconsoverwrite_sync_postgres_parquet(data: overwrite_sync_postgres_parquetParams):
    if not data.redis_queue:
        conn = await asyncpg.connect(
            user=framework.settings.Postgres_UserName,
            host=framework.settings.Postgres_Host,
            port=framework.settings.Postgres_Port,
            password=framework.settings.Postgres_password,
            database=framework.settings.databaseName
        )
        try:
            # count = 1
            sources = await _get_source(data.reconId)
            output = f'{framework.settings.mftpath}/duckdb/{data.reconId}/year={data.exec_date.split("-")[0]}/month={str(int(data.exec_date.split("-")[1]))}/day={str(int(data.exec_date.split("-")[2]))}'
            print("output: ", output)
            if os.path.exists(output):
                # os.remove(output)
                shutil.rmtree(output, ignore_errors=True)
            print('sources: ', sources)
            for each_source in sources:
                list_of_query = [
                    f'''SELECT * FROM "{data.reconId}_matched" WHERE "SOURCE" = '{each_source}' AND "EXECUTION_STATEMENTDATE" = '{data.exec_date}';''',
                    f'''SELECT * FROM "{data.reconId}_unmatched" WHERE "SOURCE" = '{each_source}' AND "EXECUTION_STATEMENTDATE" = '{data.exec_date}';'''
                ]
                for query in list_of_query:
                    count = 1
                    # async with conn.transaction():
                    #     cursor = await conn.cursor(stmt)

                    #     while True:
                    #         records = await cursor.fetchall()

                    #         if not records:
                    #             print("In Break")
                    #             break
                    stmt = await conn.prepare(query)
                    rows = await stmt.fetch()
                    column_names = [a.name for a in stmt.get_attributes()]
                    df = pd.DataFrame(rows, columns=column_names)
                    df = pl.from_pandas(df)
                    # df = [dict(row) for row in records]
                    # df = pl.DataFrame(df)
                    print(df.filter(pl.col("family") == 'authwaiting'))
                    if f"{data.reconId}_unmatched" in query:
                        if 'authwaiting' not in df['family'].unique().to_list():
                            output = f'{framework.settings.mftpath}/duckdb/{data.reconId}/year={data.exec_date.split("-")[0]}/month={str(int(data.exec_date.split("-")[1]))}/day={str(int(data.exec_date.split("-")[2]))}/SOURCE=authwaiting/species=authwaiting'
                            print("output: ", output)
                            if os.path.exists(output):
                                # os.remove(output)
                                shutil.rmtree(output, ignore_errors=True)
                    if f"{data.reconId}_matched" in query:
                        if 'rollbackwaiting' not in df['family'].unique().to_list():
                            output = f'{framework.settings.mftpath}/duckdb/{data.reconId}/year={data.exec_date.split("-")[0]}/month={data.exec_date.split("-")[1]}/day={data.exec_date.split("-")[2]}/SOURCE=rollbackwaiting/species=rollbackwaiting'
                            print("output: ", output)
                            if os.path.exists(output):
                                # os.remove(output)
                                shutil.rmtree(output, ignore_errors=True)
                    df = df.with_columns(
                        [
                            pl.col('EXECUTION_STATEMENTDATE').dt.year().alias('year'),
                            pl.col('EXECUTION_STATEMENTDATE').dt.month().alias('month'),
                            pl.col('EXECUTION_STATEMENTDATE').dt.day().alias('day'),
                        ]
                    )
                    df = df.with_columns(
                            pl.when(~pl.col("family").is_in(['matched', 'unmatched', 'dropped', 'failed', 'duplicated', 'selfmatched']))
                            .then(pl.col("family"))
                            .otherwise(pl.col("SOURCE"))
                            .alias("SOURCE")
                        )
                    df = df.to_pandas()
                    df['Json Data'] = df['Json Data'].apply(json.loads)
                    if '__index_level_0_' in df.columns.tolist():
                        del df['__index_level_0_']
                    if '__index_level_0__' in df.columns.tolist():
                        del df['__index_level_0__']
                    df = df.reset_index()
                    df = df.join(pd.json_normalize(df['Json Data'])).drop(columns=['Json Data'])
                    df = df.fillna("")
                    df = df.astype(str)
                    group_by_list = ['year', 'month', 'day', 'SOURCE', 'species']
                    col_rename = {col: f"{col}_{''.join(str(ord(c)) for c in col)}" for i, col in enumerate(df.columns) if col not in group_by_list}
                    df.rename(columns=col_rename, inplace=True)
                    partitions = df.groupby(['year', 'month', 'day', 'SOURCE', 'species'])
                    for partition, df in partitions:
                        partition_path = f'{framework.settings.mftpath}/duckdb/{data.reconId}/'
                        table = pa.Table.from_pandas(df)
                        pq.write_to_dataset(
                            table,
                            root_path=partition_path,
                            existing_data_behavior='delete_matching' if count == 1 else None,
                            partition_cols=['year', 'month', 'day', 'SOURCE', 'species']
                        )
                        count += 1

        finally:
            await conn.close()

        return {
            "status": True, "message": "Sync Completed", "data": []
        }

    else:
        await redis_queue._RedisQueue('assetProcessor').put(
            jsonpickle.dumps({"op":"Overwrite_Sync_Postgres_Parquet", "data": {"reconId": data.reconId, "exec_date": data.exec_date}}))
        return {
            "status": True, "message": "Sync Started.", "data": []
        }


async def _get_recons():
    recons_ins = recons_stdapi.Recons()
    params = framework.queryparams.QueryParams()
    params.limit = 100
    params.skip = 0
    params.q = json.dumps({})
    resp = await recons_ins.get_all(params, framework.settings.dbName)
    resp = resp.get("data", [])
    recon_ids = []
    for each_recon in resp:
        if not isinstance(each_recon, dict):
            each_recon = each_recon.__dict__
        recon_ids.append(each_recon.get("reconId", ""))
    recon_ids = [item for item in recon_ids if item]
    return recon_ids

async def _get_source(reconId: str):
    query = {"reconId": reconId}
    params = framework.queryparams.QueryParams()
    params.limit = 100
    params.skip = 0
    params.q = json.dumps(query)
    resp = await SourceReference_stdapi.SourceReference.get_all(params, framework.settings.dbName)
    resp = resp.get("data", [])
    sources = []
    for each_source in resp:
        sources.append(each_source.get("source", ""))
    return sources