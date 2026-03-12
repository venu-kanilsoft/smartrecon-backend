from MasterDataCrosswalk_enum import *
from MasterDataCrosswalk_model import *
import framework
import typing
import framework.settings
import fastapi
import os
import shutil
import MasterDataCrosswalk_stdapi

router = fastapi.APIRouter(prefix='/masterdatacrosswalk')

@router.post('/uploadMasterDataCrosswalk', tags=['MasterDataCrosswalk'])
async def MasterDataCrosswalkuploadMasterDataCrosswalk(file: fastapi.UploadFile = fastapi.File(...), uniqueId: typing.Optional[str] = None):
    crosswalk_path = os.path.join(framework.settings.mftpath, "crosswalk")
    if uniqueId:
        masterdata_ins = MasterDataCrosswalk_stdapi.MasterDataCrosswalk()
        master_data = await masterdata_ins.get(uniqueId)

        if not master_data['versionNumber']:
            master_data['versionNumber'] = 1
        else:
            master_data['versionNumber'] += 1
        master_filename = master_data['fileName'].split(".")[0] + '_version' + str(master_data['versionNumber']) + "." + master_data['fileName'].split(".")[-1]
        shutil.copy(crosswalk_path + "/" + master_data['fileName'], crosswalk_path + '/' + master_filename)
        key = 'version_' + str(master_data['versionNumber'])
        if not master_data['versionDetails']:
            master_data['versionDetails'] = {key: master_data['fileName']}
        else:
            master_data['versionDetails'].update({key: master_data['fileName']})
        # master_data['fileName'] = file.filename
        data_object = masterdata_ins.parse_obj(master_data)
        await data_object.update(framework.settings.dbName)

    filename = file.filename
    file_contents = await file.read()
    
    if not os.path.exists(crosswalk_path):
        os.makedirs(crosswalk_path)
    finalfilename = os.path.join(crosswalk_path, filename)
    with open(finalfilename, "wb") as f:
        f.write(file_contents)
    
    return {"status": True, "message": "Succesfully uploaded", "data": []}