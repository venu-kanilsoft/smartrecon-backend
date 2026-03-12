from MasterDataCrosswalk_enum import *
from MasterDataCrosswalk_model import *
import fastapi
import MasterDataCrosswalk_stdapi


router = fastapi.APIRouter(prefix='/masterdatacrosswalk')

@router.post('/getColumns', tags=['MasterDataCrosswalk'])
async def MasterDataCrosswalkgetColumns(data: getColumnsParams):
    master_crosswalk_ins = MasterDataCrosswalk_stdapi.MasterDataCrosswalk()
    masterdata_details = await master_crosswalk_ins.get(data.crosswalkId)

    if masterdata_details['loadType'].lower() == 'csv':
        columns = await MasterDataCrosswalk_stdapi._readcsv(masterdata_details, True)
    elif masterdata_details['loadType'].lower() == 'text':
        df = await MasterDataCrosswalk_stdapi._readcsv(masterdata_details, True)
    elif masterdata_details['loadType'].lower() == 'excel':
        columns = await MasterDataCrosswalk_stdapi._readexcel(masterdata_details, True)
    else:
        return {"status": False, "message": "Only CSV and Excel is allowed", "data": []}
    
    if isinstance(columns, list):
        return {"status": True, "message": "Success", "data": columns}
    return columns