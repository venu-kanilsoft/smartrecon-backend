from email import message
import os
from pydoc import doc
from reconexecution_enum import *
import reconexecution_model 
import recons_stdapi
import fastapi
import datetime
import framework
import SystemAudit_stdapi

router = fastapi.APIRouter(prefix='/reconexecution')

@router.post('/runrecon', tags=['ReconExecution'])
async def ReconExecutionrunrecon(data: reconexecution_model.runreconParams):
    fmt_stmtdate = datetime.datetime.strptime(data.stmtdate, '%d-%m-%Y').strftime('%d-%b-%Y')

    # createdBy = flask.session['sessionData']['email']
    login_session = await framework.restapi.me()
    createdBy = login_session.get('email', '')

    sysdfp = os.path.join('/etc/systemd/system', data.reconId + '.service')    
    if os.path.exists(sysdfp):        
        return {"status": False, "message": "Recon Execution is already in progress or a stale job exists."}

    #engine_scripts_path = framework.settings.engine_scripts_path
    engine_scripts_path = framework.settings.polars_engine_path
    if not engine_scripts_path:
        engine_scripts_path = "/data/ngerecon/smartrecon/reconengine/scripts_polars"
    cmd = f"{engine_scripts_path}/reconexec.sh {data.reconId} {fmt_stmtdate} {createdBy}"
    with open(sysdfp, 'w') as f:
        lines = list()
        lines.append('[Unit]\n')
        lines.append('Description=Recon Job Service\n\n')
        lines.append('[Service]\n')
        lines.append('Type=simple\n')
        lines.append(f'WorkingDirectory={engine_scripts_path}\n')
        lines.append('ExecStart=%s\n' % cmd)
        lines.append('ExecStop=/bin/rm -rf %s\n' % sysdfp)
        f.writelines(lines)

    os.system('systemctl daemon-reload')
    os.system('systemctl start "%s.service"' % data.reconId)

    recondata = await recons_stdapi.Recons.get(data.reconId)
    recondata = recondata
    doc = {'type': 'Recon Execution', 'msg': f'Execution initiated statementdate:{fmt_stmtdate} for {recondata["reconName"]}',
                     'reason': 'Success', 'actionStatus': True, 'email': createdBy, 'reconId': data.reconId}
    status, message = await SystemAudit_stdapi.create_auditLogs(doc=doc)
    return {"status": True, "message": "Recon Execution in progress please check status in Jobs"}
