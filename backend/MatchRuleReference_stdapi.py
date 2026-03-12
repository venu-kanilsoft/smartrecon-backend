
import framework.postgresmodel
import framework.queryparams
import framework.types
from MatchRuleReference_enum import *
from MatchRuleReference_model import *
import fastapi
router = fastapi.APIRouter()


















@router.post('/matchrulereference', response_model=MatchRuleReference, tags=['MatchRuleReference'])
async def create(inputObj: MatchRuleReferenceCreate):
    
    return await inputObj.create()





@router.put('/matchrulereference', response_model=MatchRuleReference, tags=['MatchRuleReference'])
async def update(inputObj: MatchRuleReference):
    
    
    return await inputObj.update()


@router.get('/matchrulereference/{id}', response_model=MatchRuleReference, tags=['MatchRuleReference'])
async def get(id: str):
    return await MatchRuleReference.get(id)


@router.get('/matchrulereference', response_model=MatchRuleReferenceGetResp, tags=['MatchRuleReference'])
async def get_all(response: fastapi.Response, params = fastapi.Depends(framework.queryparams.QueryParams)):
    if params.download:
        response.headers['Content-Disposition'] = f'attachment; filename="matchrulereference.html"'
    return await MatchRuleReference.get_all(params)


@router.delete('/matchrulereference/{id}', tags=['MatchRuleReference'])
async def delete(id: str):
    return await MatchRuleReference.delete(id)

