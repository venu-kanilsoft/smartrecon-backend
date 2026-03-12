from recons_enum import *
from recons_model import *
import fastapi
import pandas
import json
import sys
import recons_stdapi
import reconexecdetailslog_getlatestexedetails
sys.path.append(framework.settings.engine_scripts_path)
import Matcher

router = fastapi.APIRouter(prefix='/recons')

@router.post('/get_similar_matches', tags=['Recons'])
async def Reconsget_similar_matches(data: get_similar_matchesParams):
    s1matchcols = []
    s2matchcols = []
    for query in data.match_query:
        s1matchcols.append(query['s1colname'])
        s2matchcols.append(query['s2colname'])

    s1data = pandas.DataFrame(json.loads(data.records))
    # Reading second source data from file
    data1 = reconexecdetailslog_getlatestexedetails.getLatestExeDetailsParams
    data1.reconId = data.reconId
    doc = await reconexecdetailslog_getlatestexedetails.ReconExecDetailsLoggetLatestExeDetails(data1)
    if not doc['status']:
        return {"status": False, "message": "Unable to find latest execution details", "data": []}
        
    stmtdate = doc["data"][0].get('statementDate', None).strftime('%d%m%Y')
    resp = await recons_stdapi._get_data(data.reconId, stmtdate, "unmatched", source=data.source)
    if not resp['status']:
        return {"status": resp['status'], "message": resp['message'], "data": []}
    
    # Reading the original source data
    s2data = pandas.DataFrame(json.loads(resp['data']))
    if len(s1data)>0 and len(s2data)>0:
        # sending for matching
        left,right = Matcher.Matcher().match(s1data, s2data, leftmatchColumns=s1matchcols, rightmatchColumns=s2matchcols)
        rightmatched = right[right["MATCHING_STATUS"] == "MATCHED"]
        if not rightmatched.empty:
            rightmatched.fillna('', inplace=True)
            return {"status": True, "message": "Success", "data": json.dumps(rightmatched.to_dict(orient='records'))}
    else:
        return {"status": False, "message":"No records in selected source.", "data": []}
    return {"status": False, "message":"No Similar Records Found", "data": []}