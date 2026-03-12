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
import MasterDataCrosswalkAudit_enum



class MasterDataCrosswalkAuditCreate(framework.postgresmodel.BasePostgresModel):
    fileName: str
    displayName: str
    remarks: str
    comments: str
    UserId: str
    # approvedBy: str

    class Config:
        collection_name = 'masterdata_crosswalk_audit'
    
    

class MasterDataCrosswalkAudit(framework.postgresmodel.PostgresModel):
    fileName: typing.Optional[str]
    displayName: typing.Optional[str]
    remarks: typing.Optional[str]
    comments: typing.Optional[str]
    UserId: typing.Optional[str]
    # approvedBy: typing.Optional[str]
    
    class Config:
        collection_name = 'masterdata_crosswalk_audit'
    

    

    


class MasterDataCrosswalkAuditGetResp(pydantic.BaseModel):
    data: typing.List[MasterDataCrosswalkAudit]
    total: int = pydantic.Field(0)
    count: int = pydantic.Field(0)

