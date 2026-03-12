
import framework.postgresmodel
import framework.queryparams
import framework.types
from MasterDataCrosswalk_enum import *
from MasterDataCrosswalk_model import *
import MasterDataCrosswalkAudit_stdapi
# import NotificationAlert_stdapi
import os
import json
import pandas
import fastapi
import datetime
import framework.settings
router = fastapi.APIRouter()


@router.post('/masterdatacrosswalk', response_model=MasterDataCrosswalkCreateUpdateGetResp, tags=['MasterDataCrosswalk'])
async def create(inputObj: MasterDataCrosswalkCreate):
    query = {"displayName": inputObj.displayName}
    params = framework.queryparams.QueryParams()
    params.limit = None
    params.q = json.dumps(query)
    params.sort = json.dumps({"updated": -1})
    params.fields = None
    resp = await MasterDataCrosswalk.get_all(params, framework.settings.dbName)
    if resp['data']:
        return {"status": False, "message": "Crosswalk Name already exists", "data": []}

    login_session = await framework.restapi.me()
    inputObj.createdBy = login_session.get("email", "")

    masterdata_audit_ins = MasterDataCrosswalkAudit_stdapi.MasterDataCrosswalkAudit()
    audit_doc = {
        "fileName" : inputObj.fileName,
        "displayName" : inputObj.displayName,
        "remarks" : "Crosswalk Created",
        "comments" : "Crosswalk uploaded for first time",
        "UserId" : login_session.get("email", "")
        # approvedBy = login_session.get("email", "")
    }
    data_object = masterdata_audit_ins.parse_obj(audit_doc)
    await data_object.create(framework.settings.dbName)

    notification_ins = NotificationAlert_stdapi.NotificationAlert()
    for each_user in inputObj.needToApprove:
        notification_doc = {
            "notificationType": "Crosswalk Uploaded",
            "notificationDetails": "Crosswalk has been uploaded.",
            "notificationAssignedTo": each_user,
            "notificationAssignedBy": login_session.get("email", ""),
            "notificationAssignedDate": datetime.datetime.now().isoformat(),
            "notificationStatus": "Open"
        }
        data_object = notification_ins.parse_obj(notification_doc)
        await data_object.create(framework.settings.dbName)
    return await inputObj.create()





@router.put('/masterdatacrosswalk', response_model=MasterDataCrosswalkCreateUpdateGetResp, tags=['MasterDataCrosswalk'])
async def update(inputObj: MasterDataCrosswalk):
    login_session = await framework.restapi.me()
    inputObj.updatedBy = login_session.get("email", "")
    if login_session.get("email", "") in inputObj.needToApprove:
        return {"status": True, "message": "Same user cannot approve crosswalk", "data": []}
    # inputObj.isApproved = False
    # inputObj.approvedBy = ''

    masterdata_audit_ins = MasterDataCrosswalkAudit_stdapi.MasterDataCrosswalkAudit()
    audit_doc = {
        "fileName" : inputObj.fileName,
        "displayName" : inputObj.displayName,
        "remarks" : "Crosswalk Updated",
        "comments" : inputObj.comments,
        "UserId" : login_session.get("email", "")
        # approvedBy = login_session.get("email", "")
    }
    data_object = masterdata_audit_ins.parse_obj(audit_doc)
    await data_object.create(framework.settings.dbName)
    
    notification_ins = NotificationAlert_stdapi.NotificationAlert()
    for each_user in inputObj.needToApprove:
        notification_doc = {
            "notificationType": "Crosswalk Updated",
            "notificationDetails": "Crosswalk has been updated.",
            "notificationAssignedTo": each_user,
            "notificationAssignedBy": login_session.get("email", ""),
            "notificationAssignedDate": datetime.datetime.now(),
            "notificationStatus": "Open"
        }
        data_object = notification_ins.parse_obj(notification_doc)
        await data_object.create(framework.settings.dbName)

    return await inputObj.update()


@router.get('/masterdatacrosswalk/{id}', response_model=MasterDataCrosswalk, tags=['MasterDataCrosswalk'])
async def get(id: str):
    return await MasterDataCrosswalk.get(id)


@router.get('/masterdatacrosswalk', response_model=MasterDataCrosswalkGetResp, tags=['MasterDataCrosswalk'])
async def get_all(response: fastapi.Response, params = fastapi.Depends(framework.queryparams.QueryParams)):
    if params.download:
        response.headers['Content-Disposition'] = f'attachment; filename="masterdatacrosswalk.html"'
    return await MasterDataCrosswalk.get_all(params)


@router.delete('/masterdatacrosswalk/{id}', tags=['MasterDataCrosswalk'])
async def delete(id: str, comments: str):
    login_session = await framework.restapi.me()
    masterdata_details = await MasterDataCrosswalk.get(id)
    masterdata_audit_ins = MasterDataCrosswalkAudit_stdapi.MasterDataCrosswalkAudit()
    audit_doc = {
        "fileName" : masterdata_details['fileName'],
        "displayName" : masterdata_details['displayName'],
        "remarks" : "Crosswalk Deleted",
        "comments" : comments,
        "UserId" : login_session.get("email", "")
        # approvedBy = login_session.get("email", "")
    }
    data_object = masterdata_audit_ins.parse_obj(audit_doc)
    await data_object.create(framework.settings.dbName)

    notification_ins = NotificationAlert_stdapi.NotificationAlert()
    notification_doc = {
        "notificationType": "Crosswalk Deleted",
        "notificationDetails": "Crosswalk has been Deleted.",
        "notificationAssignedTo": login_session.get("email", ""),
        "notificationAssignedBy": login_session.get("email", ""),
        "notificationAssignedDate": datetime.datetime.now(),
        "notificationStatus": "Open"
    }
    data_object = notification_ins.parse_obj(notification_doc)
    await data_object.create(framework.settings.dbName)

    return await MasterDataCrosswalk.delete(id)



async def _readcsv(data, getColumns=False, previousVersion=None):
    file_path = os.path.join(framework.settings.mftpath, "crosswalk", data['fileName'])
    if previousVersion:
        file_path = os.path.join(framework.settings.mftpath, "crosswalk", data["versionDetails"][previousVersion])
    if not os.path.exists(file_path):
        return {"status": False, "message": "File Not Found", "data": []}
    if getColumns:
        df = pandas.read_csv(
            file_path,
            sep=data['delimiter'],
            nrows=0
        )
        return df.columns.tolist()
    df = pandas.read_csv(
        file_path, 
        sep=data['delimiter'], 
        dtype=str
    )
    return {"status": True, "message": "Success", "data": df}


async def _readexcel(data, getColumns=False, previousVersion=None):
    file_path = os.path.join(framework.settings.mftpath, "crosswalk", data['fileName'])
    if previousVersion:
        file_path = os.path.join(framework.settings.mftpath, "crosswalk", data["versionDetails"][previousVersion])
    if not os.path.exists(file_path):
        return {"status": False, "message": "File Not Found", "data": []}
    if getColumns:
        df = pandas.read_excel(
            file_path,
            sheet_name=data['sheetName'] if data['sheetName'] else None, 
            nrows=0
        )
        return df.columns.tolist()
    df = pandas.read_excel(
        file_path, 
        sheet_name=data['sheetName'] if data['sheetName'] else None, 
        dtype='str'
    )
    return {"status": True, "message": "Success", "data": df}