from recons_enum import *
from recons_model import *
import fastapi
import os
import json
import glob
import pyminizip
import recons_stdapi
import SourceReference_stdapi
import Flows_stdapi
import FeedFile_stdapi
import zipfile

router = fastapi.APIRouter(prefix='/recons')

@router.post('/downloadRecons', tags=['Recons'])
async def ReconsdownloadRecons(data: downloadReconsParams):
    dbName = framework.settings.dbName
    path = os.path.join('/data/ngerecon/mft/downloads', data.reconId)
    recons_ins = recons_stdapi.Recons()
    # Recons
    query = {"reconId": data.reconId}
    params = framework.queryparams.QueryParams()
    params.limit = 10
    params.q = json.dumps(query)
    newrecondef = await recons_ins.get_all(params, dbName)
    print(newrecondef)
    if newrecondef.get('data', []):
        newrecondef = newrecondef.get('data', [])
        path = os.path.join('/data/ngerecon/mft/downloads', data.reconId)
        if not os.path.exists(path):
            os.makedirs(path)
        print(path)
        with open(os.path.join(path,"recons.json"), "w") as final:
            json.dump(newrecondef, final)
    # Source Reference
    query = {"reconId": data.reconId}
    params = framework.queryparams.QueryParams()
    params.limit = 100
    params.skip = 0
    params.q = json.dumps(query)
    sourceins = SourceReference_stdapi.SourceReference()
    resp = await sourceins.get_all(params, framework.settings.dbName)
    if resp.get('data', []):
        resp = resp.get('data', [])
        for each_source in resp:
            master_data = each_source.get("masterMergeData", [])
            if master_data:
                if not isinstance(master_data, list):
                    master_data = [master_data]
                for each_master in master_data:
                    query = {"master_id": each_master["source"]}
                    params.q = json.dumps(query)
                    master_resp = await sourceins.get_all(params, framework.settings.dbName)
                    resp = resp + master_resp.get("data", [])
        path = os.path.join('/data/ngerecon/mft/downloads', data.reconId)
        if not os.path.exists(path):
            os.makedirs(path)
        with open(os.path.join(path,"sourcereference.json"), "w") as final:
            json.dump(resp, final)
    # Flows
    query = {"reconId": data.reconId}
    params = framework.queryparams.QueryParams()
    params.limit = 100
    params.skip = 0
    params.q = json.dumps(query)
    flowsins = Flows_stdapi.Flows()
    resp = await flowsins.get_all(params, framework.settings.dbName)
    if resp.get('data', []):
        resp = resp.get('data', [])
        path = os.path.join('/data/ngerecon/mft/downloads', data.reconId)
        if not os.path.exists(path):
            os.makedirs(path)
        with open(os.path.join(path,"flows.json"), "w") as final:
            json.dump(resp, final)
    # FeedFile
    query = {"reconId": data.reconId}
    params = framework.queryparams.QueryParams()
    params.limit = 100
    params.skip = 0
    params.q = json.dumps(query)
    feedfile_ins = FeedFile_stdapi.FeedFile()
    resp = await feedfile_ins.get_all(params, framework.settings.dbName)
    if resp.get('data', []):
        resp = resp.get('data', [])
        path = os.path.join('/data/ngerecon/mft/downloads', data.reconId)
        if not os.path.exists(path):
            os.makedirs(path)
        with open(os.path.join(path,"feedfile.json"), "w") as final:
            json.dump(resp, final)

    # Added by Shrihari
    for file in os.listdir(path):
        if file.endswith('.zip'):
            os.remove(os.path.join(path, file))

    zipfp = os.path.join(path, data.reconId + '.zip')
    compression_level = 9
    os.chdir(path)
    print('zipfp -->',zipfp)
    pyminizip.compress_multiple(os.listdir(path), [], zipfp, "password", compression_level)
    if not os.path.exists('/usr/share/nginx/newsmartrecon/postgresui/downloads/'):
        os.system('ln -s /data/ngerecon/mft/downloads/ /usr/share/nginx/newsmartrecon/postgresui/')
    return {"status": True, "data": '/downloads/' + data.reconId + '/'  + data.reconId + '.zip', "message": "Success"}
    
