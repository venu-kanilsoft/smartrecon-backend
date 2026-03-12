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
import MasterDataCrosswalk_enum



class MasterDataCrosswalkCreate(framework.postgresmodel.BasePostgresModel):
    fileName: str
    displayName: str
    loadType: str
    delimiter: typing.Optional[str] = pydantic.Field("", **{})
    sheetName: typing.Optional[str] = pydantic.Field("", **{})
    createdBy: typing.Optional[str] = pydantic.Field("", **{})
    updatedBy: typing.Optional[str] = pydantic.Field("", **{})
    comments: typing.Optional[str] = pydantic.Field("", **{})
    isApproved: typing.Optional[bool] = pydantic.Field(False, )
    approvedBy: typing.Optional[str] = pydantic.Field("", **{})
    needToApprove: typing.Optional[typing.List[str]] = pydantic.Field([], **{})
    approvedDateTime: typing.Optional[datetime.date]
    versionNumber: typing.Optional[int] = pydantic.Field(0, **{})
    versionDetails: typing.Optional[dict] = pydantic.Field({}, **{})
    isFileUploaded: typing.Optional[bool] = pydantic.Field(False, )

    class Config:
        collection_name = 'masterdata_crosswalk'
    
    

class MasterDataCrosswalk(framework.postgresmodel.PostgresModel):
    fileName: typing.Optional[str]
    displayName: typing.Optional[str]
    loadType: typing.Optional[str]
    delimiter: typing.Optional[str] = pydantic.Field("", **{})
    sheetName: typing.Optional[str] = pydantic.Field("", **{})
    createdBy: typing.Optional[str] = pydantic.Field("", **{})
    updatedBy: typing.Optional[str] = pydantic.Field("", **{})
    comments: typing.Optional[str] = pydantic.Field("", **{})
    isApproved: typing.Optional[bool] = pydantic.Field(False, )
    approvedBy: typing.Optional[str] = pydantic.Field("", **{})
    needToApprove: typing.Optional[typing.List[str]] = pydantic.Field([], **{})
    approvedDateTime: typing.Optional[datetime.date]
    versionNumber: typing.Optional[int] = pydantic.Field(0, **{})
    versionDetails: typing.Optional[dict] = pydantic.Field({}, **{})
    isFileUploaded: typing.Optional[bool] = pydantic.Field(False, )
    
    class Config:
        collection_name = 'masterdata_crosswalk'
    

    
class MasterDataCrosswalkCreateUpdateGetResp(pydantic.BaseModel):
    data: MasterDataCrosswalk
    status: bool = pydantic.Field("True")
    message: str = pydantic.Field("Success")
    total: int = pydantic.Field(0)
    count: int = pydantic.Field(0)
    


class MasterDataCrosswalkGetResp(pydantic.BaseModel):
    data: typing.List[MasterDataCrosswalk]
    status: bool = pydantic.Field("True")
    message: str = pydantic.Field("Success")
    total: int = pydantic.Field(0)
    count: int = pydantic.Field(0)
class getMasterDataCrosswalkDataParams(pydantic.BaseModel):
    crosswalkId: str
    previousVersion: typing.Optional[str] = pydantic.Field("", **{})
    filters: typing.Optional[dict] = pydantic.Field({}, **{})
    
    
class uploadMasterDataCrosswalkParams(pydantic.BaseModel):
    
    
    pass
    

class getColumnsParams(pydantic.BaseModel):
    crosswalkId: str


class downloadCrosswalkParams(pydantic.BaseModel):
    fileName: str


class approveCrosswalkParams(pydantic.BaseModel):
    crosswalkId: str
    comments: str