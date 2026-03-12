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
import reconexecution_enum



class ReconExecutionCreate(framework.postgresmodel.BasePostgresModel):

    class Config:
        collection_name = 'reconexecution'
    
    

class ReconExecution(framework.postgresmodel.PostgresModel):
    
    class Config:
        collection_name = 'reconexecution'
    

    

    


class ReconExecutionGetResp(pydantic.BaseModel):
    data: typing.List[ReconExecution]
    total: int = pydantic.Field(0)
    count: int = pydantic.Field(0)
class uploadinputdataParams(pydantic.BaseModel):
    

    pass
    
    
class runreconsParams(pydantic.BaseModel):
    stmtdate: str
    reconids: typing.List[str]
    
    
class runreconParams(pydantic.BaseModel):
    stmtdate: str
    reconId: str
    
    
class rollbackParams(pydantic.BaseModel):
    reconId: str
    
    

