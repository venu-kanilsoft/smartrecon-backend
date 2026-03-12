from recons_enum import *
from recons_model import *
import fastapi
import string
import json

router = fastapi.APIRouter(prefix='/recons')

@router.post('/updateReconRemarksFromFile', tags=['Recons'])
async def ReconsupdateReconRemarksFromFile(data: updateReconRemarksFromFileParams, file: fastapi.UploadFile = fastapi.File(...)):
    uploadpath = os.path.join(framework.settings.mftpath, 'remarks')
    if not os.path.exists(uploadpath):
        os.makedirs(uploadpath)
    filename = file.filename
    file_contents = await file.read()
    finalfilename = os.path.join(uploadpath, filename)
    with open(finalfilename, "wb") as f:
        f.write(file_contents)
    
    self.rq = RedisQueue("remarks")
    doc={'recon_id':recon_id,'filename':finalfilename}
    self.rq.put(json.dumps({"op": "remarksupload", "data": doc}))
    time.sleep(30)
    return {"status": True,"message": "Comments are started uploading", "data": []}