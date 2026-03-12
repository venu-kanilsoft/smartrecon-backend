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
import GlBalance_enum



class GlBalanceCreate(framework.postgresmodel.BasePostgresModel):
    AccountNumber: str
    AccountName: str
    reconId: str
    reconName: str
    reconProcess: str
    sourceName: str
    stmtDate: str
    CLOSING_BAL: str
    OPENING_BAL: str
    ExecutionId: str
    Currency: str

    class Config:
        collection_name = 'gl_balance'
    
    

class GlBalance(framework.postgresmodel.PostgresModel):
    AccountNumber: typing.Optional[str]
    AccountName: typing.Optional[str]
    reconId: typing.Optional[str]
    reconName: typing.Optional[str]
    reconProcess: typing.Optional[str]
    sourceName: typing.Optional[str]
    stmtDate: typing.Optional[str]
    CLOSING_BAL: typing.Optional[str]
    OPENING_BAL: typing.Optional[str]
    ExecutionId: typing.Optional[str]
    Currency: typing.Optional[str]
    
    class Config:
        collection_name = 'gl_balance'
    

    

    


class GlBalanceGetResp(pydantic.BaseModel):
    data: typing.List[GlBalance]
    total: int = pydantic.Field(0)
    count: int = pydantic.Field(0)
class getGlBalanceParams(pydantic.BaseModel):
    recon_id: str
    accnum: typing.Optional[typing.List[str]] = pydantic.Field([], **{})
    stmtdate: typing.Optional[str] = pydantic.Field("", **{})
    
    

