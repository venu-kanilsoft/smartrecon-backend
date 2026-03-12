
import framework.postgresmodel
import framework.queryparams
import framework.types
from ReconSummary_enum import *
from ReconSummary_model import *
import fastapi
router = fastapi.APIRouter()




@router.post('/reconsummary', response_model=ReconSummary, tags=['ReconSummary'])
async def create(inputObj: ReconSummaryCreate):
    
    return await inputObj.create()





@router.put('/reconsummary', response_model=ReconSummary, tags=['ReconSummary'])
async def update(inputObj: ReconSummary):
    
    
    return await inputObj.update()


@router.get('/reconsummary/{id}', response_model=ReconSummary, tags=['ReconSummary'])
async def get(id: str):
    return await ReconSummary.get(id)


@router.get('/reconsummary', response_model=ReconSummaryGetResp, tags=['ReconSummary'])
async def get_all(response: fastapi.Response, params = fastapi.Depends(framework.queryparams.QueryParams)):
    if params.download:
        response.headers['Content-Disposition'] = f'attachment; filename="reconsummary.html"'
    return await ReconSummary.get_all(params)


@router.delete('/reconsummary/{id}', tags=['ReconSummary'])
async def delete(id: str):
    return await ReconSummary.delete(id)

