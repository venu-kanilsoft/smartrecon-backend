import datetime

import asyncpg
import jsonpickle

from recons_enum import *
from recons_model import *
import json
import duckdb
import fastapi
import framework
import redis_queue
import polars as pl
import pandas as pd
import pyarrow as pa
import recons_stdapi
import framework.restapi
import pyarrow.parquet as pq

router = fastapi.APIRouter(prefix='/recons')


@router.post('/update_postgres_parquet', tags=['Recons'])
async def Reconsupdate_postgres_parquet(data: update_postgres_parquetParams):
    if not data.redis_queue:
        con = duckdb.connect()
        try:
            update_df = pd.DataFrame(json.loads(data.records))
            exec_date = datetime.datetime.strptime(data.exec_date, "%Y-%m-%d")
            year, month, day = exec_date.year, exec_date.month, exec_date.day
            basepath = f'{framework.settings.mftpath}duckdb'
            db_df = con.execute(
                f"SELECT * FROM read_parquet('{basepath}/*/*/*/*/*/*.parquet', hive_partitioning=True) "
                f"WHERE year = {year} AND month {month} AND day = {day};"
            ).fetchdf()
            db_df = db_df[~db_df['_id'].isin(update_df['_id'].tolist())]
            db_df = db_df.append(update_df)
            group_by_list = ['year', 'month', 'day', 'SOURCE', 'species']
            col_rename = {col: f"{col}_{''.join(str(ord(c)) for c in col)}" for i, col in enumerate(db_df.columns) if col not in group_by_list}
            db_df.rename(columns=col_rename, inplace=True)
            partitions = db_df.groupby(['year', 'month', 'day', 'SOURCE', 'species'])
            for partition, db_df in partitions:
                partition_path = f'{framework.settings.mftpath}/duckdb/{data.reconId}/'
                table = pa.Table.from_pandas(db_df)
                pq.write_to_dataset(
                    table,
                    root_path=partition_path,
                    partition_cols=['year', 'month', 'day', 'SOURCE', 'species']
                )
        finally:
            con.close()
        return {
            "status": True, "message": "Update Record Completed", "data": []
        }

    else:
        doc = {
            "reconId": data.reconId,
            "exec_date": data.exec_date,
            "records": data.records
        }
        await redis_queue._RedisQueue('assetProcessor').put(
            jsonpickle.dumps({"op": "Update_Postgres_Parquet", "tenant": framework.ctx['tenant'], "data": doc}))
        return {
            "status": True, "message": "Sync Started.", "data": []
        }
