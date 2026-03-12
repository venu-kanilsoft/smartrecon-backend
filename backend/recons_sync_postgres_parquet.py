import asyncpg
import jsonpickle

from recons_enum import *
from recons_model import *
import json
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


# @router.post('/sync_postgres_parquet', tags=['Recons'])
# async def Reconssync_postgres_parquet(data: sync_postgres_parquetParams):
#     if not data.redis_queue:
#         conn = await asyncpg.connect(
#             user=framework.settings.Postgres_UserName,
#             host=framework.settings.Postgres_Host,
#             port=framework.settings.Postgres_Port,
#             password=framework.settings.Postgres_password,
#             database=framework.settings.databaseName
#         )
#         if not data.reconId:
#             recon_ids = await _get_recons()
#         else:
#             recon_ids = [data.reconId]
#         try:
#             for reach_recon in recon_ids:
#                 stmt = f'SELECT * FROM "{reach_recon}"'
#                 print("stmt: ", stmt)

#                 async with conn.transaction():
#                     cursor = await conn.cursor(stmt)

#                     while True:
#                         records = await cursor.fetch(1000000)

#                         if not records:
#                             break

#                         df = [dict(row) for row in records]
#                         df = pl.DataFrame(df)
#                         df = df.with_columns(
#                             [
#                                 pl.col('EXECUTION_STATEMENTDATE').dt.year().alias('year'),
#                                 pl.col('EXECUTION_STATEMENTDATE').dt.month().alias('month'),
#                                 pl.col('EXECUTION_STATEMENTDATE').dt.day().alias('day'),
#                             ]
#                         )
#                         df = df.with_columns(
#                             pl.when(~pl.col("family").is_in(['matched', 'unmatched', 'dropped', 'failed', 'duplicated', 'selfmatched', 'authwaiting', 'rollbackwaiting', 'recon_summary', 'gl_recon_summary']))
#                             .then(pl.col("family"))
#                             .otherwise(pl.col("SOURCE"))
#                             .alias("SOURCE")
#                         )
#                         df = df.fill_null("")
#                         df = df.to_pandas()
#                         df = df[df['family'] != 'gl_recon_summary']
#                         df = df[df['family'] != 'recon_summary']
#                         df['Json Data'] = df['Json Data'].apply(json.loads)
#                         if '__index_level_0_' in df.columns.tolist():
#                             del df['__index_level_0_']
#                         if '__index_level_0__' in df.columns.tolist():
#                             del df['__index_level_0__']
#                         # df = df.reset_index()
#                         print(df)
#                         df = df.join(pd.json_normalize(df['Json Data'])).drop(columns=['Json Data'])
#                         # if 'level_0' in df.columns:
#                         #     del df['level_0']
#                         df = df.reset_index()
#                         df.rename(columns={"Source": "SummarySource"}, inplace=True)
#                         df = df.astype(str)
#                         group_by_list = ['year', 'month', 'day', 'SOURCE', 'species']
#                         # col_rename = {col: f'{col}_{i}' for i, col in enumerate(df.columns) if col not in group_by_list}
#                         col_rename = {col: f"{col}_{''.join(str(ord(c)) for c in col)}" for i, col in enumerate(df.columns) if col not in group_by_list}
#                         df.rename(columns=col_rename, inplace=True)
#                         partitions = df.groupby(['year', 'month', 'day', 'SOURCE', 'species'])
#                         for partition, df in partitions:
#                             partition_path = f'{framework.settings.mftpath}/duckdb/{reach_recon}/'
#                             table = pa.Table.from_pandas(df)
#                             pq.write_to_dataset(
#                                 table,
#                                 root_path=partition_path,
#                                 partition_cols=['year', 'month', 'day', 'SOURCE', 'species']
#                             )

#         finally:
#             await conn.close()

#         return {
#             "status": True, "message": "Sync Completed", "data": []
#         }

#     else:
#         await redis_queue._RedisQueue('assetProcessor').put(
#             jsonpickle.dumps({"op":"Sync_Postgres_Parquet", "tenant": framework.ctx['tenant'], "data": {"reconId": data.reconId}}))
#         return {
#             "status": True, "message": "Sync Started.", "data": []
#         }

@router.post('/sync_postgres_parquet', tags=['Recons'])
async def Reconssync_postgres_parquet(data: sync_postgres_parquetParams):
    if not data.redis_queue:
        conn = await asyncpg.connect(
            user=framework.settings.Postgres_UserName,
            host=framework.settings.Postgres_Host,
            port=framework.settings.Postgres_Port,
            password=framework.settings.Postgres_password,
            database=framework.settings.databaseName
        )
        if not data.reconId:
            recon_ids = await _get_recons()
        else:
            recon_ids = [data.reconId]
        try:
            for reach_recon in recon_ids:
                sources = await _get_source(reach_recon)
                for each_source in sources:
                    list_of_query = [
                        f'''SELECT * FROM "{data.reconId}_matched" WHERE "SOURCE" = '{each_source}';''',
                        f'''SELECT * FROM "{data.reconId}_unmatched" WHERE "SOURCE" = '{each_source}';'''
                    ]
                    print("list_of_query: ", list_of_query)
                    for stmt in list_of_query:
                        count = 1
                        async with conn.transaction():
                            cursor = await conn.cursor(stmt)

                            while True:
                                records = await cursor.fetch(1000000)

                                if not records:
                                    break

                                df = [dict(row) for row in records]
                                df = pl.DataFrame(df)
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
                                # col_rename = {col: f'{col}_{i}' for i, col in enumerate(df.columns) if col not in group_by_list}
                                col_rename = {col: f"{col}_{''.join(str(ord(c)) for c in col)}" for i, col in enumerate(df.columns) if col not in group_by_list}
                                df.rename(columns=col_rename, inplace=True)
                                partitions = df.groupby(group_by_list)
                                for partition, df in partitions:
                                    partition_path = f'{framework.settings.mftpath}/duckdb/{reach_recon}/'
                                    table = pa.Table.from_pandas(df)
                                    pq.write_to_dataset(
                                        table,
                                        root_path=partition_path,
                                        partition_cols=group_by_list,
                                        existing_data_behavior='delete_matching' if count == 1 else None,
                                    )
                                count += 1
        finally:
            await conn.close()

        return {
            "status": True, "message": "Sync Completed", "data": []
        }

    else:
        await redis_queue._RedisQueue('assetProcessor').put(
            jsonpickle.dumps({"op":"Sync_Postgres_Parquet", "tenant": framework.ctx['tenant'], "data": {"reconId": data.reconId}}))
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