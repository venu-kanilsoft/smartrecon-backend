from MasterDataCrosswalk_enum import *
from MasterDataCrosswalk_model import *
import fastapi
import os
import openpyxl



router = fastapi.APIRouter(prefix='/masterdatacrosswalk')

@router.post('/getSheetName', tags=['MasterDataCrosswalk'])
async def MasterDataCrosswalkgetSheetName(file: fastapi.UploadFile = fastapi.File(...)):
    filename = file.filename
    file_contents = await file.read()
    crosswalk_path = os.path.join("/tmp/")
    if not os.path.exists(crosswalk_path):
        os.makedirs(crosswalk_path)
    finalfilename = os.path.join(crosswalk_path, filename)
    with open(finalfilename, "wb") as f:
        f.write(file_contents)
    
    if filename.split(".")[-1] != 'xlsx':
        return {"status": False, "message": "Success", "data": []}
    
    workbook = openpyxl.load_workbook(finalfilename)
    sheetnames = workbook.sheetnames
    workbook.close()
    if os.path.exists(finalfilename):
        os.remove(finalfilename)
    return {"status": True, "message": "Success", "data": sheetnames}