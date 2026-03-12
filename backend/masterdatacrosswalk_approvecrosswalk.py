from MasterDataCrosswalk_enum import *
from MasterDataCrosswalk_model import *
import MasterDataCrosswalkAudit_stdapi
import MasterDataCrosswalk_stdapi
# import NotificationAlert_stdapi
import framework.settings
import framework
import fastapi
import shutil
import os

router = fastapi.APIRouter(prefix='/masterdatacrosswalk')

@router.post('/approveCrosswalk', tags=['MasterDataCrosswalk'])
async def MasterDataCrosswalkapproveCrosswalk(data: approveCrosswalkParams):
    master_crosswalk_ins = MasterDataCrosswalk_stdapi.MasterDataCrosswalk()
    masterdata_details = await master_crosswalk_ins.get(data.crosswalkId)

    login_session = await framework.restapi.me()
    if login_session.get("email", "") not in masterdata_details['needToApprove']:
        return {"status": False, "message": "Your not allowed to aprrove crosswalk.", "data": []}
    
    if masterdata_details['isApproved']:
        return {"status": False, "message": "Crosswalk has already approved. Cannot approve again."}

    masterdata_details['isApproved'] = True
    masterdata_details['approvedBy'] = login_session.get("email", "")
    masterdata_details['approvedDateTime'] = datetime.datetime.now().isoformat()
    data_object = master_crosswalk_ins.parse_obj(masterdata_details)
    await data_object.update(framework.settings.dbName)

    masterdata_audit_ins = MasterDataCrosswalkAudit_stdapi.MasterDataCrosswalkAudit()
    audit_doc = {
        "fileName" : masterdata_details['fileName'],
        "displayName" : masterdata_details['displayName'],
        "remarks" : "Crosswalk Approve",
        "comments" : data.comments,
        "UserId" : login_session.get("email", "")
        # approvedBy = login_session.get("email", "")
    }
    data_object = masterdata_audit_ins.parse_obj(audit_doc)
    await data_object.create(framework.settings.dbName)

    notification_ins = NotificationAlert_stdapi.NotificationAlert()
    notification_doc = {
        "notificationType": "Crosswalk Approved",
        "notificationDetails": "Crosswalk has been approved.",
        "notificationAssignedTo": masterdata_details['updatedBy'],
        "notificationAssignedBy": login_session.get("email", ""),
        "notificationAssignedDate": datetime.datetime.now(),
        "notificationStatus": "Open"
    }
    data_object = notification_ins.parse_obj(notification_doc)
    await data_object.create(framework.settings.dbName)

    return {"status": True, "message": "Crosswalk approved", "data": []}