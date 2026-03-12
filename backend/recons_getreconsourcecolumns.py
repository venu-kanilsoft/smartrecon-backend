from recons_enum import *
from recons_model import *
import fastapi
import json
import recons_stdapi
import SourceReference_stdapi
import Flows_stdapi

router = fastapi.APIRouter(prefix='/recons')

@router.post('/getReconSourceColumns', tags=['Recons'])
async def ReconsgetReconSourceColumns(data: getReconSourceColumnsParams):
    source_cols = {}
    recons_ins = recons_stdapi.Recons()
    newrecondef = await recons_ins.get(data.reconId, framework.settings.dbName)
    recondata =  newrecondef
    if not recondata:
        return {"status": False, "message": "Unable to find recon details", "data": []}
    reconsources = recondata.get('sources', [])
    for src in reconsources:
        # finding the source reference of this source
        query = {"reconId": data.reconId,"_id": src}
        flowsquery = {"reconId": data.reconId}
        params = framework.queryparams.QueryParams()
        params.limit = 1
        params.fields = None
        params.skip = 0
        
        params.q = json.dumps(query)                
        print("query --->",query)
        resp = await SourceReference_stdapi.SourceReference().get_all(params, framework.settings.dbName)
        params.q = json.dumps(flowsquery)
        
        # Shrihari
        flows_resp = await Flows_stdapi.Flows().get_all(params, framework.settings.dbName)
        flows = flows_resp.get('data', [])[0]
        print('Flows -->',flows)
                                                            
        if not resp.get('data', []):
            continue
        sourceref = resp.get('data', [])[0]
        cols = []
        feed = sourceref.get('feedDetails', [])
        for fd in feed:
            if fd.get('required', False):
                if 'UIDisplayName' in fd:
                    cols.append(fd['UIDisplayName'])
                    cols.append('SOURCE')
                    cols.append('MATCHING_STATUS')
                    cols.append('STATEMENT_DATE')
                    cols.append('AGEING')
        srcname = sourceref.get('source', '')
        cols += sourceref.get("derivedColumns", [])
        
        # Shrihari
        for node in flows['nodes']:
            if node['name'] == "VLookup" and node['properties']['data'].split('.')[-1] == srcname:
                cols.extend(node['properties']['includeCols'])
                                
        source_cols[srcname] = list(set(cols))                
    source_cols['_conditions'] = ["Exact Match", "Contains"]
    return {"status":True, "message": "Success", "data":source_cols}
