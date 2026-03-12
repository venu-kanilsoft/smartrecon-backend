from re import template
from reconnotificationrule_enum import *
from reconnotificationrule_model import *
import fastapi
import os
import glob


router = fastapi.APIRouter(prefix='/reconnotificationrule')

@router.post('/listOfTemplates', tags=['ReconNotificationRule'])
async def ReconNotificationRulelistOfTemplates(data: listOfTemplatesParams):
    template_path = os.path.join(framework.settings.engine_scripts_path, 'mail_templates')
    list_of_templates = []
    if os.path.exists(template_path):
        for files in glob.glob("*.html"):
            list_of_templates.append(files)
    return {"status": True, "message": "Success", "data": list_of_templates}
