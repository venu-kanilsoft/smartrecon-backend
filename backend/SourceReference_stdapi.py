
import framework.postgresmodel
import framework.queryparams
import framework.types
from SourceReference_enum import *
from SourceReference_model import *
import fastapi
router = fastapi.APIRouter()




































@router.post('/sourcereference', response_model=SourceReference, tags=['SourceReference'])
async def create(inputObj: SourceReferenceCreate):
    
    return await inputObj.create()





@router.put('/sourcereference', response_model=SourceReference, tags=['SourceReference'])
async def update(inputObj: SourceReference):
    
    
    return await inputObj.update()


@router.get('/sourcereference/{id}', response_model=SourceReference, tags=['SourceReference'])
async def get(id: str):
    return await SourceReference.get(id)


@router.get('/sourcereference', response_model=SourceReferenceGetResp, tags=['SourceReference'])
async def get_all(response: fastapi.Response, params = fastapi.Depends(framework.queryparams.QueryParams)):
    if params.download:
        response.headers['Content-Disposition'] = f'attachment; filename="sourcereference.html"'
    return await SourceReference.get_all(params)


@router.delete('/sourcereference/{id}', tags=['SourceReference'])
async def delete(id: str):
    return await SourceReference.delete(id)

