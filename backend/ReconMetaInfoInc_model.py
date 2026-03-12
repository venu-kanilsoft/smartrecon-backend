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
import ReconMetaInfoInc_enum



class IncCreate(framework.postgresmodel.BasePostgresModel):
    source: typing.Optional[str] = pydantic.Field("", **{})
    incrementLoader: typing.Optional[str] = pydantic.Field("", **{})
    disableCarryForward: typing.Optional[bool] = pydantic.Field(False, )

    
    





class ReconMetaInfoIncCreate(framework.postgresmodel.BasePostgresModel):
    reconName: str
    reconId: str
    incData: typing.Optional[typing.List[IncCreate]]

    class Config:
        collection_name = 'recon_meta_info_inc'
    
    

class ReconMetaInfoInc(framework.postgresmodel.PostgresModel):
    reconName: typing.Optional[str]
    reconId: typing.Optional[str]
    incData: typing.Optional[typing.List[IncCreate]]
    
    class Config:
        collection_name = 'recon_meta_info_inc'
    

    

    


class ReconMetaInfoIncGetResp(pydantic.BaseModel):
    data: typing.List[ReconMetaInfoInc]
    total: int = pydantic.Field(0)
    count: int = pydantic.Field(0)

