from Glmapping_enum import *
from Glmapping_model import *
import fastapi
import zipfile
import pandas

router = fastapi.APIRouter(prefix='/glmapping')

@router.post('/gluploadinputdata', tags=['Glmapping'])
async def Glmappinggluploadinputdata(data: gluploadinputdataParams, file: fastapi.UploadFile = fastapi.File(...)):
    uploadpath = os.path.join(framework.settings.mftpath, 'glmapping', data.recon_id)
    if not os.path.exists(uploadpath):
        os.makedirs(uploadpath)
    filename = file.filename
    file_contents = await file.read()
    finalfilename = os.path.join(uploadpath, filename)
    with open(finalfilename, "wb") as f:
        f.write(file_contents)
    
    if finalfilename.endswith('.zip'):
        with zipfile.ZipFile(finalfilename, 'r') as zip_ref:
            zip_ref.extractall(uploadpath)
        os.remove(finalfilename)
    
    fileName = os.listdir(uploadpath)
    for files in fileName:
        glfilepath = os.path.join(uploadpath,files)
        if os.path.isfile(glfilepath):
            ext = glfilepath.split('.')[1]
            if ext == 'csv':
                GlData = pandas.read_csv(glfilepath)
            if ext == 'xlsx':
                GlData = pandas.read_excel(glfilepath)
            for x in GlData.columns:
                GlData[x]=GlData[x].astype(str).str.strip()
    if len(GlData)>0:
        GlData['reconId'] = data.recon_id
        if set(['glNumber','glName']).issubset(GlData.columns):
            ins = framework.postgresmodel.PostgresModel()
            status = await ins.insert_df(
                                GlData,
                                "glName",
                                family="glmapping",
                                species="glmapping",
                                indexName=framework.settings.dbName,
                            )
            return {"status": True, "message": "Gl Data Uploaded successfully", "data": []}
        else:
            return {"status":False, "message": "glNumber or glName columns are not present", "data": []}
    else:
        return {"status":False, "message": "File is empty", "data": []}