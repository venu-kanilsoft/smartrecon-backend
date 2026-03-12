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
import ReconExecDetailsLog_enum



class rollbackReconQueryCreate(framework.postgresmodel.BasePostgresModel):
    statementDate: typing.Optional[str] = pydantic.Field("", **{})
    reconName: typing.Optional[str] = pydantic.Field("", **{})

    
    





class ReconExecDetailsLogCreate(framework.postgresmodel.BasePostgresModel):
    statementDate: datetime.datetime
    jobStatus: str
    errorMsg: str
    reconName: str
    reconProcess: str
    reconId: str
    reconExecutionId: str
    stmtDate: int
    executionDateTime: str
    executedBy: str
    rollbackedBy: str
    cycleName: typing.Optional[str] = pydantic.Field("", **{})

    class Config:
        collection_name = 'recon_exec_details_log'
    
    

class ReconExecDetailsLog(framework.postgresmodel.PostgresModel):
    statementDate: typing.Optional[datetime.datetime]
    jobStatus: typing.Optional[str]
    errorMsg: typing.Optional[str]
    reconName: typing.Optional[str]
    reconProcess: typing.Optional[str]
    reconId: typing.Optional[str]
    reconExecutionId: typing.Optional[str]
    stmtDate: typing.Optional[int]
    executionDateTime: typing.Optional[str]
    executedBy: typing.Optional[str]
    rollbackedBy: typing.Optional[str]
    cycleName: typing.Optional[str] = pydantic.Field("", **{})
    
    class Config:
        collection_name = 'recon_exec_details_log'
    

    

    


class ReconExecDetailsLogGetResp(pydantic.BaseModel):
    data: typing.List[ReconExecDetailsLog]
    total: int = pydantic.Field(0)
    count: int = pydantic.Field(0)
class getLatestExeDetailsParams(pydantic.BaseModel):
    reconId: str
    
    
class getMaxReconExecutionDocParams(pydantic.BaseModel):
    recon_names: typing.List[str]
    
    
class rollbackReconParams(pydantic.BaseModel):
    query: rollbackReconQueryCreate
    
    
class get_latest_execution_detailsParams(pydantic.BaseModel):
    
    
    pass
    

