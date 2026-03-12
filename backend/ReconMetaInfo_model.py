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
import ReconMetaInfo_enum



class ReportDetailCreate(framework.postgresmodel.BasePostgresModel):
    displayName: typing.Optional[str] = pydantic.Field("", **{})
    filename: typing.Optional[str] = pydantic.Field("", **{})
    source: typing.Optional[str] = pydantic.Field("", **{})

    
    


class IncCreate(framework.postgresmodel.BasePostgresModel):
    source: typing.Optional[str] = pydantic.Field("", **{})
    incrementLoader: typing.Optional[str] = pydantic.Field("", **{})
    disableCarryForward: typing.Optional[bool] = pydantic.Field(False, )

    
    





class GetReportCreate(framework.postgresmodel.BasePostgresModel):
    displayname: str
    filename: str
    source: str

    
    





class ReconMetaInfoCreate(framework.postgresmodel.BasePostgresModel):
    reconName: str
    reconProcess: str
    reconId: str
    reportDetails: typing.List[ReportDetailCreate]
    statementDate: datetime.date
    stmtdate: int
    reconExecutionId: int
    cycleWise: str

    class Config:
        collection_name = 'recon_meta_info'
    
    

class ReconMetaInfo(framework.postgresmodel.PostgresModel):
    reconName: typing.Optional[str]
    reconProcess: typing.Optional[str]
    reconId: typing.Optional[str]
    reportDetails: typing.Optional[typing.List[ReportDetailCreate]]
    statementDate: typing.Optional[datetime.date]
    stmtdate: typing.Optional[int]
    reconExecutionId: typing.Optional[int]
    cycleWise: typing.Optional[str]
    
    class Config:
        collection_name = 'recon_meta_info'
    

    

    


class ReconMetaInfoGetResp(pydantic.BaseModel):
    data: typing.List[ReconMetaInfo]
    total: int = pydantic.Field(0)
    count: int = pydantic.Field(0)




class ReconMetaInfoIncCreate(framework.postgresmodel.BasePostgresModel):
    reconName: str
    reconId: str
    incData: typing.List[IncCreate]

    class Config:
        collection_name = 'reconMetaInfo'
    
    

class ReconMetaInfoInc(framework.postgresmodel.PostgresModel):
    reconName: typing.Optional[str]
    reconId: typing.Optional[str]
    incData: typing.Optional[typing.List[IncCreate]]
    
    class Config:
        collection_name = 'reconMetaInfo'
    

    

    


class ReconMetaInfoIncGetResp(pydantic.BaseModel):
    data: typing.List[ReconMetaInfoInc]
    total: int = pydantic.Field(0)
    count: int = pydantic.Field(0)





class ReconReportCreate(framework.postgresmodel.BasePostgresModel):
    reconName: str
    reconId: str
    reconProcess: str
    stmtdate: datetime.date
    reportDetails: typing.List[GetReportCreate]

    class Config:
        collection_name = 'ReconReport'
    
    

class ReconReport(framework.postgresmodel.PostgresModel):
    reconName: typing.Optional[str]
    reconId: typing.Optional[str]
    reconProcess: typing.Optional[str]
    stmtdate: typing.Optional[datetime.date]
    reportDetails: typing.Optional[typing.List[GetReportCreate]]
    
    class Config:
        collection_name = 'ReconReport'
    

    

    


class ReconReportGetResp(pydantic.BaseModel):
    data: typing.List[ReconReport]
    total: int = pydantic.Field(0)
    count: int = pydantic.Field(0)
