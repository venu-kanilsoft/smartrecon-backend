from MasterDataCrosswalk_enum import *
from MasterDataCrosswalk_model import *
import framework.settings
import framework
import fastapi
import shutil
import os

router = fastapi.APIRouter(prefix='/masterdatacrosswalk')

@router.post('/downloadCrosswalk', tags=['MasterDataCrosswalk'])
async def MasterDataCrosswalkdownloadCrosswalk(data: downloadCrosswalkParams):
    file_path = os.path.join(framework.settings.mftpath, "crosswalk", data.fileName)
    if not os.path.exists(file_path):
        return {"status": False, "message": "File Not Found", "data": []}
    
    login_session = await framework.restapi.me()
    userid = login_session.get('given_name')
    downloadpath = os.path.join(framework.settings.mftpath, 'downloads', userid)
    if not os.path.exists(downloadpath):
        os.makedirs(downloadpath)
    
    # creating link to downloads folder
    if not os.path.exists(f'{framework.settings.ui_path}downloads'):
        os.system(f'ln -s {framework.settings.mftpath}downloads/ {framework.settings.ui_path}')

    shutil.copy(file_path, downloadpath)
    return {"status": True, "message":"Success", "data": os.path.join('/downloads', userid, data.fileName)}