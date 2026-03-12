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
import Glmapping_enum



class GlmappingCreate(framework.postgresmodel.BasePostgresModel):
    reconName: str
    reconProcess: str
    reconId: str
    glNumber: str
    glName: str

    class Config:
        collection_name = 'gl_mapping'
    
    

class Glmapping(framework.postgresmodel.PostgresModel):
    reconName: typing.Optional[str]
    reconProcess: typing.Optional[str]
    reconId: typing.Optional[str]
    glNumber: typing.Optional[str]
    glName: typing.Optional[str]
    
    class Config:
        collection_name = 'gl_mapping'
    

    

    


class GlmappingGetResp(pydantic.BaseModel):
    data: typing.List[Glmapping]
    total: int = pydantic.Field(0)
    count: int = pydantic.Field(0)
class gluploadinputdataParams(pydantic.BaseModel):
    recon_id: str
    
    

