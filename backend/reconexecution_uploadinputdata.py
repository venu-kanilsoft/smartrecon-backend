from reconexecution_enum import *
from reconexecution_model import *
import fastapi
import zipfile

router = fastapi.APIRouter(prefix='/reconexecution')

@router.post('/uploadinputdata', tags=['ReconExecution'])
async def ReconExecutionuploadinputdata(file: fastapi.UploadFile = fastapi.File(...)):
    uploadpath = os.path.join(framework.settings.mftpath, 'sources')
    if not os.path.exists(uploadpath):
        os.makedirs(uploadpath)
    filename = file.filename
    file_contents = await file.read()
    finalfilename = os.path.join(uploadpath, filename)
    ext = os.path.split(finalfilename)[1].split('.')[1]
    if ext != 'zip':
        return {"status":False, "message":"Only zip files are allowed", "data": []}
    with open(finalfilename, "wb") as f:
        f.write(file_contents)
    
    if finalfilename.endswith('.zip'):
        with zipfile.ZipFile(finalfilename, 'r') as zip_ref:
            zip_ref.extractall(uploadpath)
        os.remove(finalfilename)
    return {"status": True, "message": "Input Data Uploaded successfully", "data": []}