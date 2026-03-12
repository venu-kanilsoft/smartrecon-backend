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
import first_enum



class SmartreconCreate(framework.postgresmodel.BasePostgresModel):
    name: str = pydantic.Field(**{'max_length': 256, 'min_length': 3})
    description: str

    class Config:
        collection_name = 'test'
    
    

class Smartrecon(framework.postgresmodel.PostgresModel):
    name: typing.Optional[str] = pydantic.Field(**{'max_length': 256, 'min_length': 3})
    description: typing.Optional[str]
    
    class Config:
        collection_name = 'test'
    

    

    


class SmartreconGetResp(pydantic.BaseModel):
    data: typing.List[Smartrecon]
    total: int = pydantic.Field(0)
    count: int = pydantic.Field(0)





class ReconExecDetailsLogCreate(framework.postgresmodel.BasePostgresModel):
    reconId: str

    class Config:
        collection_name = 'recon_execution_details_log'
    
    

class ReconExecDetailsLog(framework.postgresmodel.PostgresModel):
    reconId: typing.Optional[str]
    
    class Config:
        collection_name = 'recon_execution_details_log'
    

    

    


class ReconExecDetailsLogGetResp(pydantic.BaseModel):
    data: typing.List[ReconExecDetailsLog]
    total: int = pydantic.Field(0)
    count: int = pydantic.Field(0)

