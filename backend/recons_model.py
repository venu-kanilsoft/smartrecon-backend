import typing
import datetime
import ipaddress
import fastapi
import pydantic
import shutil
import os
import framework.postgresmodel
import framework.queryparams
import framework.types
import recons_enum



class MatchQueryCreate(framework.postgresmodel.BasePostgresModel):
    s1colname: str
    s2colname: str
    s1colcondition: str

    
    



class ReconsCreate(framework.postgresmodel.BasePostgresModel):
    # _id: typing.Optional[str]
    id: typing.Optional[str]
    reconName: str
    reconProcess: str
    reconId: str
    sources: typing.Optional[typing.List[str]] = pydantic.Field([], **{})
    displayColumns: typing.Optional[typing.List[str]] = pydantic.Field([], **{})
    currentStmtDate: typing.Optional[str] = pydantic.Field("", **{})
    prevStmtDate: typing.Optional[str] = pydantic.Field("", **{})

    class Config:
        collection_name = 'recons'
    
    

class Recons(framework.postgresmodel.PostgresModel):
    _id: typing.Optional[str]
    # id: typing.Optional[str]
    reconName: typing.Optional[str]
    reconProcess: typing.Optional[str]
    reconId: typing.Optional[str]
    sources: typing.Optional[typing.List[str]] = pydantic.Field([], **{})
    displayColumns: typing.Optional[typing.List[str]] = pydantic.Field([], **{})
    currentStmtDate: typing.Optional[str] = pydantic.Field("", **{})
    prevStmtDate: typing.Optional[str] = pydantic.Field("", **{})
    
    class Config:
        collection_name = 'recons'
    

    

    


class ReconsGetResp(pydantic.BaseModel):
    data: typing.List[Recons]
    total: int = pydantic.Field(0)
    count: int = pydantic.Field(0)
class getSummaryColumnsParams(pydantic.BaseModel):
    
    
    pass
    
class get_mail_settingsParams(pydantic.BaseModel):
    reconId: str
    
    
class getReconSourceColumnsParams(pydantic.BaseModel):
    reconId: str
    
    
class get_similar_matchesParams(pydantic.BaseModel):
    reconId: str
    match_query: typing.List[MatchQueryCreate]
    source: str
    destination: str
    records: typing.Optional[str] = pydantic.Field("", **{})
    
    
class operationDataParams(pydantic.BaseModel):
    reconId: str
    # records: str
    records: typing.List[str]
    amountcol: str
    operation: str
    
    
class operationAllDataParams(pydantic.BaseModel):
    reconId: str
    sources: str
    stmtdate: typing.Optional[str] = pydantic.Field("", **{})
    
    
class importReconParams(pydantic.BaseModel):
    
    
    pass
    
class downloadReportParams(pydantic.BaseModel):
    reconId: str
    filename: str
    stmtdate: typing.Optional[str] = pydantic.Field("", **{})
    cyclewise: typing.Optional[str] = pydantic.Field("", **{})


class downloadAllReportParams(pydantic.BaseModel):
    reconId: str
    stmtdate: typing.Optional[str] = pydantic.Field("", **{})
    cyclewise: typing.Optional[str] = pydantic.Field("", **{})

    
class searchStringParams(pydantic.BaseModel):
    # reconId: str
    search_string: str
    # stmtdate: typing.Optional[str] = pydantic.Field("", **{})
    
    
class exportXlsxParams(pydantic.BaseModel):
    reconId: str
    reconName: str
    records: str
    operation: str
    stmtdate: typing.Optional[str] = pydantic.Field("", **{})
    
    
class exportCsvParams(pydantic.BaseModel):
    reconId: str
    reconName: str
    records: str
    operation: str
    stmtdate: typing.Optional[str] = pydantic.Field("", **{})
    
    
class getExecutionDatesParams(pydantic.BaseModel):
    reconId: str
    
    
class getSummaryParams(pydantic.BaseModel):
    reconId: str
    stmtdate: typing.Optional[str] = pydantic.Field("", **{})
    cyclewise: typing.Optional[str] = pydantic.Field("", **{})
    
    
class getGlSummaryParams(pydantic.BaseModel):
    reconId: str
    stmtdate: typing.Optional[str] = pydantic.Field("", **{})
    
    
class getGlWiseSummaryParams(pydantic.BaseModel):
    reconId: str
    glnumber: str
    stmtdate: typing.Optional[str] = pydantic.Field("", **{})
    
    
class getReportsParams(pydantic.BaseModel):
    reconId: str
    stmtdate: typing.Optional[str] = pydantic.Field("", **{})
    cyclewise: typing.Optional[str] = pydantic.Field("", **{})
    
    
class getReconDataParams(pydantic.BaseModel):
    reconId: str
    operation: str
    sourceName: str
    stmtdate: typing.Optional[str] = pydantic.Field("", **{})
    
    
class getGlReconDataParams(pydantic.BaseModel):
    reconId: str
    glnumber: str
    operation: str
    sourceName: str
    stmtdate: typing.Optional[str] = pydantic.Field("", **{})
    
    
class getReconAllDataParams(pydantic.BaseModel):
    reconId: str
    operation: str
    sourceName: str
    limit: typing.Optional[int] = pydantic.Field(5000000, **{})
    offset: typing.Optional[int] = pydantic.Field(0, **{})
    old_scroll_id: typing.Optional[str] = pydantic.Field("", **{})
    stmtdate: typing.Optional[str] = pydantic.Field("", **{})
    
    
class getGlReconAllDataParams(pydantic.BaseModel):
    reconId: str
    operation: str
    glnumber: str
    stmtdate: typing.Optional[str] = pydantic.Field("", **{})
    
    
class force_match_recordsParams(pydantic.BaseModel):
    reconId: str
    # records: str
    records: typing.List[str]
    comments: typing.Optional[str] = pydantic.Field("", **{})
    net_split: typing.Optional[bool] = pydantic.Field(False, )
    
    
class authorize_force_match_recordsParams(pydantic.BaseModel):
    reconId: str
    # records: str
    records: typing.List[str]
    comments: typing.Optional[str] = pydantic.Field("", **{})
    net_split: typing.Optional[bool] = pydantic.Field(False, )
    
    
class reject_force_match_recordsParams(pydantic.BaseModel):
    reconId: str
    # records: str
    records: typing.List[str]
    comments: typing.Optional[str] = pydantic.Field("", **{})
    net_split: typing.Optional[bool] = pydantic.Field(False, )
    
class rollback_matched_recordsParams(pydantic.BaseModel):
    reconId: str
    # records: str
    records: typing.List[str]
    comments: typing.Optional[str] = pydantic.Field("", **{})
    net_split: typing.Optional[bool] = pydantic.Field(False, )
    
    
class authorize_rollback_recordsParams(pydantic.BaseModel):
    reconId: str
    # records: str
    records: typing.List[str]
    comments: typing.Optional[str] = pydantic.Field("", **{})
    net_split: typing.Optional[bool] = pydantic.Field(False, )
    
    
class reject_rollback_recordsParams(pydantic.BaseModel):
    reconId: str
    # records: str
    records: typing.List[str]
    comments: typing.Optional[str] = pydantic.Field("", **{})
    net_split: typing.Optional[bool] = pydantic.Field(False, )
    
    
class updateReconRemarksFromFileParams(pydantic.BaseModel):
    reconId: str
    
    
class processReconParams(pydantic.BaseModel):
    reconId: str
    
    
class generateDisplayColumnsParams(pydantic.BaseModel):
    reconId: str
    
    
class deleteDataParams(pydantic.BaseModel):
    reconId: str
    
    
class getProcessReconsParams(pydantic.BaseModel):
    reconProcess: str
    
    
class cloneSelectedReconParams(pydantic.BaseModel):
    reconId: str
    
    
class saveReconParams(pydantic.BaseModel):
    
    
    pass
    
class getDisplayColumnsParams(pydantic.BaseModel):
    reconId: str
    
    
class get_mail_settingsParams(pydantic.BaseModel):
    reconId: str



class updateDataParams(pydantic.BaseModel):
    reconId: str
    records: str
    operations: str
    stmtdate: typing.Optional[str] = pydantic.Field("", **{})


class fromToDateMatchParams(pydantic.BaseModel):
    reconId: str
    reconName: str
    startdate: str
    enddate: str
    operation: str
    export: str


class dirCycleParams(pydantic.BaseModel):
    reconId: str
    stmtdate: typing.Optional[str] = pydantic.Field("", **{})
    
    
class downloadBalanceParams(pydantic.BaseModel):
    reconId: str
    startdate: str
    enddate: str
    
    
class processQueueRemarksParams(pydantic.BaseModel):
    reconId: str
    filename: str
    
    
class customReportParams(pydantic.BaseModel):
    reconId: str
    
    

    
class downloadReconsParams(pydantic.BaseModel):
    reconId: str


class journeyReportParams(pydantic.BaseModel):
    reconId: str
    stmtdate: str


class getSourceAndColumnsParams(pydantic.BaseModel):
    reconId: str

class sourceColumnsCreate(pydantic.BaseModel):
    sourceName: str
    Columns: typing.Optional[typing.List[str]] = pydantic.Field([], **{})

class downloadForceMatchRecordsParams(pydantic.BaseModel):
    reconId: str
    stmtdate: typing.Optional[str] = pydantic.Field("", **{})
    sourceColumns: typing.Optional[typing.List[sourceColumnsCreate]]
    isMatched: typing.Optional[bool] = pydantic.Field(False, )
    isUnMatched: typing.Optional[bool] = pydantic.Field(False, )

class successFailed(pydantic.BaseModel):
    success: list
    failed: list


class updateBulkForceMatchParams(pydantic.BaseModel):
    reconId: str
    stmtdate: typing.Optional[str] = pydantic.Field("", **{})
    records: typing.Optional[successFailed]
    matchrecords: typing.Optional[bool] = pydantic.Field(False, )

class updateConsolidatedReportParams(pydantic.BaseModel):
    reconId: str
    stmtdate: typing.Optional[str] = pydantic.Field("", **{})
    runbackground: typing.Optional[bool] = pydantic.Field(False, )

class sync_postgres_parquetParams(pydantic.BaseModel):
    redis_queue: typing.Optional[bool] = pydantic.Field(False, )
    reconId: typing.Optional[str] = pydantic.Field("", **{})


class overwrite_sync_postgres_parquetParams(pydantic.BaseModel):
    reconId: str
    exec_date: str
    redis_queue: typing.Optional[bool] = pydantic.Field(False, )


class update_postgres_parquetParams(pydantic.BaseModel):
    reconId: str
    exec_date: str
    records: str
    redis_queue: typing.Optional[bool] = pydantic.Field(False, )
