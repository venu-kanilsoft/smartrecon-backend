from MasterDataCrosswalk_enum import *
from MasterDataCrosswalk_model import *
import fastapi
import pandas
import MasterDataCrosswalk_stdapi

router = fastapi.APIRouter(prefix='/masterdatacrosswalk')

@router.post('/getMasterDataCrosswalkData', tags=['MasterDataCrosswalk'])
async def MasterDataCrosswalkgetMasterDataCrosswalkData(data: getMasterDataCrosswalkDataParams):
    master_crosswalk_ins = MasterDataCrosswalk_stdapi.MasterDataCrosswalk()
    masterdata_details = await master_crosswalk_ins.get(data.crosswalkId)

    if masterdata_details['loadType'].lower() == 'csv':
        df = await MasterDataCrosswalk_stdapi._readcsv(masterdata_details, previousVersion=data.previousVersion)
        df = df.get("data", pandas.DataFrame())
    elif masterdata_details['loadType'].lower() == 'text':
        df = await MasterDataCrosswalk_stdapi._readcsv(masterdata_details, previousVersion=data.previousVersion)
        df = df.get("data", pandas.DataFrame())
    elif masterdata_details['loadType'].lower() == 'excel':
        df = await MasterDataCrosswalk_stdapi._readexcel(masterdata_details, previousVersion=data.previousVersion)
        df = df.get("data", pandas.DataFrame())
    else:
        return {"status": False, "message": "Only CSV and Excel is allowed", "data": []}
    
    filter_str = None
    for key, value in data.filters.items():
        if key not in df.columns:
            return {"status": False, "message": "Columns Not present in data", "data": []}
        if not filter_str:
            filter_str = f"df['{key}'].isin({value})"
        else:
            filter_str += f" | df['{key}'].isin({value})"
    
    if filter_str:
        df = eval(f"df[{filter_str}]")
    df = df.fillna("")
    return {"status": True, "message": "Success", "data": df.to_dict(orient='records')}