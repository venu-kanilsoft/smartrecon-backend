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
import MatchRuleSumColumns_enum



class MatchRuleSumColumnsCreate(framework.postgresmodel.BasePostgresModel):
    reconId: str
    sumColumns: dict

    class Config:
        collection_name = 'match_rule_sum_columns'
    
    

class MatchRuleSumColumns(framework.postgresmodel.PostgresModel):
    reconId: typing.Optional[str]
    sumColumns: typing.Optional[dict]
    
    class Config:
        collection_name = 'match_rule_sum_columns'
    

    

    


class MatchRuleSumColumnsGetResp(pydantic.BaseModel):
    data: typing.List[MatchRuleSumColumns]
    total: int = pydantic.Field(0)
    count: int = pydantic.Field(0)

