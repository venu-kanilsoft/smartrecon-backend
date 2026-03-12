
import framework.postgresmodel
import framework.queryparams
import framework.types
from MatchRuleSumColumns_enum import *
from MatchRuleSumColumns_model import *
import fastapi
router = fastapi.APIRouter()


@router.post('/matchrulesumcolumns', response_model=MatchRuleSumColumns, tags=['MatchRuleSumColumns'])
async def create(inputObj: MatchRuleSumColumnsCreate):
    
    return await inputObj.create()





@router.put('/matchrulesumcolumns', response_model=MatchRuleSumColumns, tags=['MatchRuleSumColumns'])
async def update(inputObj: MatchRuleSumColumns):
    
    
    return await inputObj.update()


@router.get('/matchrulesumcolumns/{id}', response_model=MatchRuleSumColumns, tags=['MatchRuleSumColumns'])
async def get(id: str):
    return await MatchRuleSumColumns.get(id)


@router.get('/matchrulesumcolumns', response_model=MatchRuleSumColumnsGetResp, tags=['MatchRuleSumColumns'])
async def get_all(response: fastapi.Response, params = fastapi.Depends(framework.queryparams.QueryParams)):
    if params.download:
        response.headers['Content-Disposition'] = f'attachment; filename="matchrulesumcolumns.html"'
    return await MatchRuleSumColumns.get_all(params)


@router.delete('/matchrulesumcolumns/{id}', tags=['MatchRuleSumColumns'])
async def delete(id: str):
    return await MatchRuleSumColumns.delete(id)

