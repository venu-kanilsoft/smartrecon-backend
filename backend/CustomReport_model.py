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
import CustomReport_enum



class CustomReportDetailsCreate(framework.postgresmodel.BasePostgresModel):
    Source: typing.Optional[str] = pydantic.Field("", **{})
    StatementDate: typing.Optional[str] = pydantic.Field("", **{})
    ExecutionDateTime: typing.Optional[str] = pydantic.Field("", **{})
    STATEMENT_DATE: typing.Optional[str] = pydantic.Field("", **{})
    MatchedAmount: typing.Optional[float] = pydantic.Field(0.0, **{})
    MatchedCount: typing.Optional[int] = pydantic.Field(0, **{})
    UnMatchedAmount: typing.Optional[float] = pydantic.Field(0.0, **{})
    UnMatchedCount: typing.Optional[int] = pydantic.Field(0, **{})
    ReversalAmount: typing.Optional[float] = pydantic.Field(0.0, **{})
    ReversalCount: typing.Optional[int] = pydantic.Field(0, **{})
    CarryForwardMatchedAmount: typing.Optional[float] = pydantic.Field(0.0, **{})
    CarryForwardMatchedCount: typing.Optional[int] = pydantic.Field(0, **{})
    CarryForwardUnMatchedAmount: typing.Optional[float] = pydantic.Field(0.0, **{})
    CarryForwardUnMatchedCount: typing.Optional[int] = pydantic.Field(0, **{})
    ForceMatchedAmount: typing.Optional[float] = pydantic.Field(0.0, **{})
    ForceMatchedCount: typing.Optional[int] = pydantic.Field(0, **{})
    ClosingBalance: typing.Optional[float] = pydantic.Field(0.0, **{})

    
    





class CustomReportCreate(framework.postgresmodel.BasePostgresModel):
    reconName: str
    statementDate: str
    reconType: str
    reportName: str
    details: typing.List[CustomReportDetailsCreate]
    reconId: str

    class Config:
        collection_name = 'custom_reports'
    
    

class CustomReport(framework.postgresmodel.PostgresModel):
    reconName: typing.Optional[str]
    statementDate: typing.Optional[str]
    reconType: typing.Optional[str]
    reportName: typing.Optional[str]
    details: typing.Optional[typing.List[CustomReportDetailsCreate]]
    reconId: typing.Optional[str]
    
    class Config:
        collection_name = 'custom_reports'
    

    

    


class CustomReportGetResp(pydantic.BaseModel):
    data: typing.List[CustomReport]
    total: int = pydantic.Field(0)
    count: int = pydantic.Field(0)
class loadReportParams(pydantic.BaseModel):
    reconId: str
    
    
class getDailySettlementRptParams(pydantic.BaseModel):
    statementDate: str
    
    

class generateReportParams(pydantic.BaseModel):
    records: str
    groupBy: typing.Optional[str] = pydantic.Field("", **{})
    sheetWise: typing.Optional[bool] = pydantic.Field(False, )

class renameColumns(pydantic.BaseModel):
    columns: typing.Optional[typing.List[str]] = pydantic.Field([], **{})
    rename: typing.Optional[typing.List[str]] = pydantic.Field([], **{})

class groupByParams(pydantic.BaseModel):
    reconId: str
    source: str
    stmtdate: str
    groupby_columns: typing.List[str]
    sum_columns: typing.Optional[typing.List[str]] = pydantic.Field([], **{})
    count_columns: typing.Optional[typing.List[str]] = pydantic.Field([], **{})
    rename_columns: typing.Optional[renameColumns] = pydantic.Field({}, **{})

class selectColumns(pydantic.BaseModel):
    source: typing.Optional[str] = pydantic.Field("", **{})
    columns: typing.Optional[typing.List[str]] = pydantic.Field([], **{})

class sourceFilter(pydantic.BaseModel):
    source: typing.Optional[str] = pydantic.Field("", **{})
    filerData: typing.Optional[typing.List[str]] = pydantic.Field([], **{})

class sourceGroupby(pydantic.BaseModel):
    groupby_columns: typing.Optional[typing.List[str]] = pydantic.Field([], **{})
    sum_columns: typing.Optional[typing.List[str]] = pydantic.Field([], **{})
    count_columns: typing.Optional[typing.List[str]] = pydantic.Field([], **{})
    rename_columns: typing.Optional[renameColumns] = pydantic.Field({}, **{})

class sourceMerge(pydantic.BaseModel):
    leftOn: typing.Optional[typing.List[str]] = pydantic.Field([], **{})
    rightOn: typing.Optional[typing.List[str]] = pydantic.Field([], **{})
    leftSource: typing.Optional[str] = pydantic.Field("", **{})
    rightSource: typing.Optional[str] = pydantic.Field("", **{})
    joinType: typing.Optional[str] = pydantic.Field("", **{})

class templateParams(pydantic.BaseModel):
    reconId: str
    templateName: str
    stmtdate: typing.Optional[str] = pydantic.Field("", **{})
    order_of_execution: typing.List[str]
    selected_col: typing.Optional[typing.List[selectColumns]] = pydantic.Field({}, **{})
    filterByObj: typing.Optional[typing.List[sourceFilter]] = pydantic.Field({}, **{})
    groupByObj: typing.Optional[typing.List[sourceGroupby]] = pydantic.Field({}, **{})
    mergeByObj: typing.Optional[sourceMerge] = pydantic.Field({}, **{})
