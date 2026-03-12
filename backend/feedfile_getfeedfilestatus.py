from FeedFile_enum import *
from FeedFile_model import *
import fastapi
import pandas
import json
import FeedFile_stdapi
import pysftp
import glob
import framework
import framework.types
import SourceReference_stdapi
import feedfile_getsources
import reconexecdetailslog_getlatestexedetails
from dateutil.relativedelta import relativedelta
cnopts = pysftp.CnOpts()
cnopts.hostkeys = None

router = fastapi.APIRouter(prefix='/feedfile')

@router.post('/getFeedFileStatus', tags=['FeedFile'])
async def FeedFilegetFeedFileStatus(data: getFeedFileStatusParams):
    if not data.stmtDate:
        data1 = reconexecdetailslog_getlatestexedetails.getLatestExeDetailsParams
        data1.reconId = data.reconId
        doc = await reconexecdetailslog_getlatestexedetails.ReconExecDetailsLoggetLatestExeDetails(data1)
        if doc['status']:
            data.stmtDate = datetime.datetime.fromisoformat(
                    doc["data"][0].get('statementDate', None)).strftime('%d%m%Y')
        else:
            return {"status": False, "message": "No Latest Execution Found", "data": []}
    else:
        data.stmtDate = datetime.datetime.strptime(data.stmtDate, '%d-%m-%Y').strftime('%d%m%Y')
    stmtDate = data.stmtDate
    query = {"reconId": data.reconId}
    params = framework.queryparams.QueryParams()
    params.limit = 100
    params.skip = 0
    params.q = json.dumps(query)
    resp = await FeedFile_stdapi.FeedFile.get_all(params, framework.settings.dbName)

    if not resp.get('data', []):
        reconsources = []
    else:
        reconsources = resp.get('data', [])[0]
    feeddata = pandas.DataFrame()
    if not data.stmtDate:
        data.stmtDate = datetime.datetime.now().strftime('%d-%m-%Y')
    dataparams = feedfile_getsources.getSourcesParams
    dataparams.reconId = data.reconId
    resp = await feedfile_getsources.FeedFilegetSources(dataparams)
    localpath = '/data/tmp/sftpfiles/'
    print("reconsources: ", reconsources)
    if reconsources:
        # for sources in resp.get('data', []):
        finaldata = {'reconName': data.reconName, 'reconId': data.reconId, 'fileName': '', 'fileAvailable': 'No',
        'sourceName': "", 'reconType': data.reconProcess, 'stmtDate': data.stmtDate, 'filePattern': ''}
        if 'sftp' in reconsources and reconsources['sftp']:
            sourcetype = reconsources['sftp']
            for doc in sourcetype:
                print(doc)
                finaldata['System / Process'] = finaldata['Responsibility']= finaldata['BPCL Role Holders (RH)']= ''
                finaldata['sourceName'] = doc['sourceName']
                # if doc['sourceName'] == sources:
                if (doc['pemkey'] == '') or (doc['pemkey'] == None):
                    doc['pemkey'] = None
                else:
                    doc['pemkey'] = os.path.join(framework.settings.mftpath,'sftppemkey',doc['pemkey'])
                if doc['password'] == '':
                    doc['password'] = None
                if doc['port'] == '':
                    doc['port'] = None
                else:
                    doc['port'] = int(doc['port'])
                if data.stmtDate:
                    stmtdate = datetime.datetime.strptime(str(data.stmtDate),'%d%m%Y')
                    stmtdate = stmtdate + relativedelta(days=int(doc['tdate']),months=int(doc['tmonth']))
                    filepattern = stmtdate.strftime(doc['filePattern'])
                    finaldata['filePattern'] = filepattern
                else:
                    finaldata['filePattern'] = doc['filePattern']
                    filepattern = finaldata['filePattern']
                with pysftp.Connection(host=doc['host'], username=doc['userName'], port=doc['port'], password=doc['password'],private_key=doc['pemkey'], cnopts=cnopts) as sftp:
                    if (doc['dateFolderPattern'] != '') and ('dateFoldertdate' in doc.keys()) and ('dateFoldertmonth' in doc.keys()):
                        if data.stmtDate:
                            stmtdate = datetime.datetime.strptime(str(data.stmtDate),'%d%m%Y')
                            stmtdate = stmtdate + relativedelta(days=int(doc['dateFoldertdate']),months=int(doc['dateFoldertmonth']))
                            datefolder = stmtdate.strftime(doc['dateFolderPattern'])
                        doc['remotePath'] = os.path.join(doc['remotePath'], datefolder)
                    finaldata['remotePathPending'] = doc['remotePath']
                    finaldata['fileAvailable'] = 'No'
                    finaldata['fileName'] = ''
                    print("filepattern: ", filepattern)
                    filepattern = filepattern.replace("*.*", "")
                    if sftp.exists(doc['remotePath']):
                        for files in sftp.listdir_attr(doc['remotePath']):
                            if files.filename.startswith(filepattern):
                                finaldata['fileName'] = files.filename
                                finaldata['fileAvailable'] = 'Yes'
                                finaldata['Remark'] = ''
                if 'System / Process' in doc.keys():
                        finaldata['System / Process'] = doc['System / Process']
                if 'Responsibility' in doc.keys():
                        finaldata['Responsibility'] = doc['Responsibility']
                if 'BPCLRoleHolders' in doc.keys():
                        finaldata['BPCL Role Holders (RH)'] = doc['BPCLRoleHolders']
                finaldata = pandas.DataFrame(finaldata, index=[0])
                feeddata = feeddata.append(finaldata)
                print(feeddata)
        
        elif 'mountpoint' in reconsources and reconsources['mountpoint']:
            sourcetype = reconsources['Mount point']
            for doc in sourcetype:
                if doc['sourceName'] == sources:
                    stmtdate = datetime.datetime.strptime(str(data.stmtDate),'%d%m%Y')
                    stmtdate = stmtdate + relativedelta(days=int(doc['tdate']),months=int(doc['tmonth']))
                    filepattern = stmtdate.strftime(doc['filePattern'])
                    finaldata['filePattern'] = filepattern
                    if doc['dateFolderPattern'] != '':
                        datefolder = stmtdate.strftime(doc['dateFolderPattern'])
                        doc['remotePath'] = os.path.join(doc['remotePath'], datefolder)
                    finaldata['remotePathPending'] = doc['remotePath']
                    for files in glob.glob(finaldata['remotePathPending'] + '/' + finaldata['filePattern']):
                        finaldata['fileName'] = os.path.split(files)[1]
                        finaldata['fileAvailable'] = 'Yes'
                        finaldata['Remark'] = ''
                finaldata = pandas.DataFrame(finaldata, index=[0])
                feeddata = feeddata.append(finaldata)
        
        else:
            dataparams = feedfile_getsources.getSourcesParams
            dataparams.reconId = data.reconId
            resp = await feedfile_getsources.FeedFilegetSources(dataparams)
            print("resp: ", resp)
            for sources in resp.get('data', []):
                finaldata = {'reconName': data.reconName, 'reconId': data.reconId, 'fileName': '', 'fileAvailable': 'No',
                    'sourceName': sources, 'reconType': data.reconProcess, 'stmtDate': data.stmtDate, 'filePattern': ''}
                query = {"reconId": data.reconId,"source": sources}
                params = framework.queryparams.QueryParams()
                params.limit = 100
                params.skip = 0
                params.q = json.dumps(query)
                resp = await SourceReference_stdapi.SourceReference.get_all(params, framework.settings.dbName)
                if not resp.get('data', []):
                    return {"status":False,"message": 'Please Provide Source Details', "data": []}
                source_data = resp.get('data', [])[0]
                if source_data:
                    finaldata['filePattern'] = source_data['filePattern']
                    if source_data.get('folderName', ''):
                        finaldata['remotePathPending'] = os.path.join(framework.settings.mftpath,'sources',source_data.get('folderName', ''), stmtDate)
                    else:
                        finaldata['remotePathPending'] = os.path.join(framework.settings.mftpath,'sources')
                    if os.path.exists(finaldata['remotePathPending']):
                        for files in glob.glob(finaldata['remotePathPending'] + '/' + source_data['filePattern'].split('.*')[0]):
                            finaldata['fileName'] = os.path.split(files)[1]
                            finaldata['fileAvailable'] = 'Yes'
                            finaldata['Remark'] = ''
                finaldata = pandas.DataFrame(finaldata, index=[0])
                # feeddata = feeddata.append(finaldata)
                feeddata = pandas.concat([feeddata, finaldata])
            
    else:
        dataparams = feedfile_getsources.getSourcesParams
        dataparams.reconId = data.reconId
        resp = await feedfile_getsources.FeedFilegetSources(dataparams)
        print("resp: ", resp)
        for sources in resp.get('data', []):
            finaldata = {'reconName': data.reconName, 'reconId': data.reconId, 'fileName': '', 'fileAvailable': 'No',
                'sourceName': sources, 'reconType': data.reconProcess, 'stmtDate': data.stmtDate, 'filePattern': ''}
            query = {"reconId": data.reconId,"source": sources}
            params = framework.queryparams.QueryParams()
            params.limit = 100
            params.skip = 0
            params.q = json.dumps(query)
            resp = await SourceReference_stdapi.SourceReference.get_all(params, framework.settings.dbName)
            if not resp.get('data', []):
                return {"status":False,"message": 'Please Provide Source Details', "data": []}
            source_data = resp.get('data', [])[0]
            if source_data:
                finaldata['filePattern'] = source_data['filePattern']
                if source_data.get('folderName', ''):
                    finaldata['remotePathPending'] = os.path.join(framework.settings.mftpath,'sources',source_data.get('folderName', ''), stmtDate)
                else:
                    finaldata['remotePathPending'] = os.path.join(framework.settings.mftpath,'sources')
                if os.path.exists(finaldata['remotePathPending']):
                    for files in glob.glob(finaldata['remotePathPending'] + '/' + source_data['filePattern'].split('.*')[0]):
                        finaldata['fileName'] = os.path.split(files)[1]
                        finaldata['fileAvailable'] = 'Yes'
                        finaldata['Remark'] = ''
            finaldata = pandas.DataFrame(finaldata, index=[0])
            # feeddata = feeddata.append(finaldata)
            feeddata = pandas.concat([feeddata, finaldata])
    if 'fileAvailable' in feeddata.columns:
        if 'No' in feeddata['fileAvailable'].unique():
            feeddata['reconExecutable'] = 'No'
        else:
            feeddata['reconExecutable'] = 'Yes'

    #feeddata = feeddata.reset_index(drop=True)
    #feeddata['Remark'] = ''
    #feeddata.loc[(feeddata['fileAvailable']=='No'),'Remark'] = feeddata['filePattern'].fillna('').astype('str')+' File Missing from '+feeddata['System / Process'].fillna('').astype('str')
    #reorder = ['reconName', 'reconId', 'reconType', 'stmtDate', 'sourceName', 'filePattern', 'fileName',
    #       'remotePathPending', 'fileAvailable', 'rawInputTxnCount', 'reconExecutable', 'Remark',
    #        'Responsibility', 'BPCL Role Holders (RH)'
    #       ]
    #extra_col = [x for x in feeddata.columns.tolist() if x not in reorder]
    #reorder.extend(extra_col)
    #feeddata = feeddata.loc[:,~feeddata.columns.duplicated()].copy()
    #feeddata = feeddata.reindex(columns=reorder)

    return {"status": True, "message": "Success", "data": feeddata.to_json(orient='records')}
