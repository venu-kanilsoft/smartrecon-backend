from recons_enum import *
from recons_model import *
import os
import fastapi
import pandas
import feedfile_getsources
import recons_stdapi
import SourceReference_stdapi

router = fastapi.APIRouter(prefix='/recons')

@router.post('/fromToDateMatch', tags=['Recons'])
async def ReconsfromToDateMatch(data: fromToDateMatchParams):
    if (not data.startdate) or (not data.enddate):
        return {"status": False, "message":'Please select Start and End Date.', "data": []}
    startdate = datetime.datetime.strptime(data.startdate, '%d-%m-%Y')
    enddate = datetime.datetime.strptime(data.enddate, '%d-%m-%Y')
    # deltaDate = datetime.timedelta(days=1)
    final_df = pandas.DataFrame()
    filenamemapping = {'matched': 'matched', 'unmatched': 'unmatched', 'authwaiting': 'authwaiting',
            'rollbackwaiting': 'rollbackwaiting', 'reversal': 'reversal', 'carry-forwardmatched': 'matched',
            'carry-forwardunmatched': 'unmatched'}
    while startdate <= enddate:
        folderDate = startdate.strftime('%d%m%Y')
        outputpath = os.path.join(framework.settings.mftpath, 'OUTPUT', data.reconId, folderDate)
        if os.path.exists(outputpath):
            # status, sourcelist = FeedFile().getSources('', recon_id)
            # dataparams = feedfile_getsources.getSourcesParams
            # dataparams.reconId = data.reconId
            # resp = await feedfile_getsources.FeedFilegetSources(dataparams)
            recons_ins = recons_stdapi.Recons()
            newrecondef = await recons_ins.get(data.reconId, framework.settings.dbName)
            recondata =  newrecondef
            if recondata:
                sourcelist = recondata.get('sources', [])
            else:
                return {"status":False, "message": 'Sources Not Found', "data": []}
            for source in sourcelist:
                resp = await SourceReference_stdapi.SourceReference.get(source)
                sourceref = resp
                if not sourceref:
                    continue
                srcname = sourceref.get('source', '')
                # if srcname != data.sourceName:
                #     continue
                if data.operation == 'matched':
                    df = pandas.DataFrame()
                    # if os.path.exists(outputpath + '/' + source + '.csv'):
                    resp = await recons_stdapi._get_data(data.reconId, startdate.strftime('%d%m%Y'), filenamemapping[data.operation], source=srcname)
                    if not resp['status']:
                        return {"status": resp['status'], "message": resp['message'], "data": []}
                    df = pandas.DataFrame(resp["data"])
                    final_df = final_df.append(df)
                elif data.operation == 'unmatched':
                    df = pandas.DataFrame()
                    resp = await recons_stdapi._get_data(data.reconId, startdate.strftime('%d%m%Y'), filenamemapping[data.operation], source=srcname)
                    if not resp['status']:
                        return {"status": resp['status'], "message": resp['message'], "data": []}
                    df = pandas.DataFrame(resp["data"])
                    final_df = final_df.append(df)
                else:
                    return {"status": False, "message": 'Only Matched and UnMatched Records are allowed.', "data": []}
        startdate = startdate + datetime.timedelta(days=1)
    # userid = flask.session["sessionData"].get('_id', '')
    login_session = await framework.restapi.me()
    userid = login_session.get('given_name')
    downloadpath = os.path.join(framework.settings.mftpath, 'downloads' , userid)
    if not os.path.exists(downloadpath):
        os.makedirs(downloadpath)
    if data.export == 'xlsx':
        filename = data.reconName + '_' + data.operation +'.xlsx'
        filepath = os.path.join(downloadpath, filename)
        writer = pandas.ExcelWriter(filepath, engine='xlsxwriter')
        final_df.to_excel(writer, sheet_name=data.operation, index=False)
        writer.save()
    if data.export == 'csv':
        filename = data.reconName + '_' + data.operation +'.csv'
        final_df.to_csv(downloadpath + '/' + filename, index=False)
    if not os.path.exists('/usr/share/nginx/newsmartrecon/ui/downloads'):
        os.system('ln -s ' + os.path.join(framework.settings.mftpath, "downloads") + ' /usr/share/nginx/newsmartrecon/ui/')

    # shutil.copy(filepath, downloadpath)
    return {"status": True, "message": "Success", "data": os.path.join('/downloads', userid, filename)}