import os
import glob
import json
import asyncAssetProcessor
import framework
import pandas
import logger
import sys
import ReconExecDetailsLog_stdapi
sys.path.append(framework.settings.engine_scripts_path)
import Report

logr = logger.Logger.getInstance("smartrecon")



async def _elastic_find_one(connection_object, search_doc, sort=[], limit=1000):
    """
    custom elastic equivalent of find_one() in mongo.
    Similar param scheme except for "connection_object"
    """
    query = search_doc
    params = framework.queryparams.QueryParams()
    params.limit = limit
    params.fields = []
    params.skip = 0
    params.sort = json.dumps(sort)
    params.q = json.dumps(query)
    try:
        resp = await connection_object.get_all(params, framework.settings.dbName)
        doc = resp.get("data", [])
    except Exception as e:
        print(f"Error in get_all: {e}")
        doc = []
    if not doc:
        return {}
    return doc[0]

class RedisQue():
    def __init__(self):
        self.recon_exec_ins = ReconExecDetailsLog_stdapi.ReconExecDetailsLog()
    async def processQueueRemarks(self, recon_id,filename):
        fileext=filename.split('.')[-1]
        df = pandas.DataFrame()
        try:
            skiprows = 0
            if 'csv' in fileext:
                df = pandas.read_csv(filename)
            elif 'xls' in fileext or 'xlsx' in fileext:
                xls = pandas.ExcelFile(filename)
                # get the sheet names
                sheets = xls.sheet_names
                found = False
                foundincol = False
                for sheet in sheets:
                    # Reading all the sheets data and finding if Ops Remarks is in the sheet
                    df = pandas.read_excel(filename, sheet_name=sheet)
                    df.replace(to_replace=r'[^\x00-\x7F]+',value='',regex=True,inplace=True)
                    cols = df.columns.tolist()
                    if 'Ops Remarks' not in cols:
                        maxiter = len(df) if len(df) < 15 else 15
                        df.replace(to_replace=r'[^\x00-\x7F]+',value='',regex=True,inplace=True)
                        for i in range(0, maxiter):
                            rowcontent = df.iloc[i].fillna('0').str.strip().tolist()
                            if 'Ops Remarks' in rowcontent:
                                skiprows = i
                                found = True
                                break
                    else:
                        foundincol = True
                    if found:
                        break
                if not foundincol:
                    df.columns = df.iloc[skiprows].str.strip().tolist()
                    df = df[skiprows + 1:]
            else:
                return False, "Invalid file extention"
            if df.empty:
                return False, "No data available"
        except Exception as e:
            logr.info('Exception in loading file:%s' % e)
            return False, "Failed to load file"
        if 'Ops Remarks' not in df.columns or 'LINK_ID' not in df.columns:
            return False, 'Unable to find required columns'
        df.fillna('', inplace=True)
        # Filtering records with Ops Remarks
        df['Ops Remarks'] = df['Ops Remarks'].str.decode('UTF-8', errors='ignore')
        df['Ops Remarks'] = df['Ops Remarks'].fillna('')
        # df['Ops Remarks'] = df['Ops Remarks'].str.strip()
        if df.empty:
            return False, "No comments to upload"
        # df['LINK_ID'] = df['LINK_ID'].str.strip("'")
        recon_exec_data = await _elastic_find_one(
                                self.recon_exec_ins,
                                {"reconId": self.reconID, "jobStatus": "Success"},
                                sort={"stmtDate": -1},
                                limit=1,
                            )
        if not recon_exec_data:
            return False, "Unable to find latest execution details"
        stmtdate = recon_exec_data.get('statementDate', None).strftime('%d%m%Y')
        mftpath = framework.settings.mftpath
        reportdf=pandas.DataFrame()
        for unmatchedfilename in glob.glob(os.path.join(mftpath, 'OUTPUT', recon_id, stmtdate, '*_UnMatched.csv')):
            unmatcheddf=pandas.read_csv(unmatchedfilename)
            df=df[['LINK_ID','Ops Remarks','Recon Remarks']]
            finaldf=pandas.merge(unmatcheddf,df,on=['LINK_ID'],how='left',suffixes=('','_y'),indicator=True)
            finaldf=finaldf[finaldf['_merge']=='both']
            del finaldf['Ops Remarks']
            del finaldf['Recon Remarks']
            finaldf.rename(columns={'Ops Remarks_y':'Ops Remarks','Recon Remarks_y':'Recon Remarks'},inplace=True)
            for col in finaldf.columns:
                if '_y' in col:
                    del finaldf[col]
            #reportdf=reportdf.append(finaldf)
            reportdf = pandas.concat([reportdf,finaldf],ignore_index=True)
        reportdata = list(self.mclient['report_data'].find({"reconId": recon_id}))
        if reportdata:
            for doc in reportdata:
                payload = {'uploadremarks':True,'statementDate':recon_exec_data.get('statementDate', None),'reconId':recon_id,'reportdf':reportdf,'filename':filename.split('/')[-1]}
                status,fileName = Report.Report().reportbuilder(payload,doc)
                if status:
                    return True,"Recon comments updated"
                else:
                    return False, "Failed to update comments"
        return False, 'Failed to update comments'



if __name__ == '__main__':
    q = asyncAssetProcessor._RedisQueue("remarks")
    while True:
        eventdata = q.get()
        if eventdata:
            eventdata = json.loads(eventdata)
            logr.info("REDIS Queue eventdata:%s" % eventdata)
            if eventdata['op']=='remarksupload':
                data=eventdata['data']
                (st,msg)=RedisQue().processQueueRemarks(data['recon_id'],data['filename'])
                logr.info("status after executing processQueueRemarks---->")
                logr.info(st,msg)




