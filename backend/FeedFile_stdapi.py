
import framework.postgresmodel
import framework.queryparams
import framework.types
from FeedFile_enum import *
from FeedFile_model import *
import fastapi
router = fastapi.APIRouter()






@router.post('/feedfile', response_model=FeedFile, tags=['FeedFile'])
async def create(inputObj: FeedFileCreate):
    
    return await inputObj.create()





@router.put('/feedfile', response_model=FeedFileCreateUpdateGetResp, tags=['FeedFile'])
async def update(inputObj: FeedFile):
    
    
    return await inputObj.update()


@router.get('/feedfile/{id}', response_model=FeedFile, tags=['FeedFile'])
async def get(id: str):
    return await FeedFile.get(id)


@router.get('/feedfile', response_model=FeedFileGetResp, tags=['FeedFile'])
async def get_all(response: fastapi.Response, params = fastapi.Depends(framework.queryparams.QueryParams)):
    if params.download:
        response.headers['Content-Disposition'] = f'attachment; filename="feedfile.html"'
    return await FeedFile.get_all(params)


@router.delete('/feedfile/{id}', tags=['FeedFile'])
async def delete(id: str):
    return await FeedFile.delete(id)

