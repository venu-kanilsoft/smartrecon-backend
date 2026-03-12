import fastapi
import string
import random
import pyminizip
import shutil
import json
import os
import bson
import traceback
from recons_enum import *
from recons_model import *
import recons_stdapi
import SourceReference_stdapi
import MatchRuleSumColumns_stdapi
import MatchRuleReference_stdapi
import Flows_stdapi
import FeedFile_stdapi
import SourceData_stdapi
import ColumnDataTypes_stdapi
router = fastapi.APIRouter(prefix="/recons")

dbName = framework.settings.dbName

def read_json_data(filename):
    data = []
    try:
        with open(filename, "r") as file:
            data = json.load(file)
    except Exception as e:
        print(traceback.print_exc())
        print("Error while reading file:", e)
        data = []
    return data


@router.post("/importRecon", tags=["Recons"])
async def ReconsimportRecon(file: fastapi.UploadFile = fastapi.File(...)):
    dbName = framework.settings.dbName
    filename = file.filename
    file_contents = await file.read()
    finalfilename = os.path.join("/tmp/", filename)
    with open(finalfilename, "wb") as f:
        f.write(file_contents)
    # with open(finalfilename, "wb") as buffer:
    #     shutil.copyfileobj(file.file, buffer)
    #     os.chmod(finalfilename, 0o666)

    letters = string.ascii_lowercase
    result_str = "".join(random.choice(letters) for i in range(8))
    extractpath = "/tmp/%s" % result_str

    os.makedirs(extractpath)
    # uncompress the file
    try:
        pyminizip.uncompress(finalfilename, "password", extractpath, 0)
    except Exception as e:
        print(traceback.print_exc())
        shutil.rmtree(extractpath)
        return {"status": False, "message":"Unable to extract file please upload correct file", "data": []}

    if not os.path.exists(extractpath):
        shutil.rmtree(extractpath)
        return {"status":False, "message":"File extract failed", "data": []}

    extracted_filenames = os.listdir(extractpath)
    success = []
    failure = [
        os.path.splitext(i)[0] for i in extracted_filenames
    ]  # add everything as failure initially
    for extracted_filename in extracted_filenames:
        name = os.path.join(extractpath, extracted_filename)
        raw_file_data = read_json_data(name)
        if not raw_file_data:
            print(f"Empty data in file: {extracted_filename}. Skipping DB insert")
            continue
        if not isinstance(raw_file_data, list):
            print(f"Extracted data from file: {extracted_filename} is not an array. Skipping DB insert")
            continue
        for file_data in raw_file_data:
            # print(file_data)
            # if not isinstance(file_data, dict):
            file_data["id"] = file_data["_id"]
            if isinstance(file_data.get("_id", {}), dict):
                if file_data.get("_id", {}).get("$oid"):
                    file_data["id"] = file_data["_id"] = file_data.get("_id", {}).get("$oid")
            filename_no_extension = os.path.splitext(extracted_filename)[0]

            if extracted_filename == "recons.json":
                file_data.pop("currentStmtDate", None)
                file_data.pop("prevStmtDate", None)
                recon_id = file_data.get("reconId")

                try:
                    data = await recons_stdapi.get(recon_id)
                    print(data)
                    if isinstance(data, dict):
                        if 'found' in data.keys() and not data['found']:
                            data = {}
                except Exception as e:
                    print(traceback.print_exc())
                    print("Exception while getting recon details:", e)
                    data = {}
                try:
                    if data:
                        recon_data_object = recons_stdapi.Recons.parse_obj(file_data)
                        await recon_data_object.update(dbName)
                    else:
                        print('create')
                        file_data['_id'] = file_data['reconId']
                        file_data['id'] = file_data['reconId']
                        #if "id" in file_data:
                        #    del file_data['id']
                        print("file_data_Recons ---->",file_data)
                        recon_data_object = recons_stdapi.ReconsCreate.parse_obj(file_data)
                        await recon_data_object.create(dbName)
                    success.append(filename_no_extension)
                    failure.remove(filename_no_extension)
                except Exception as e:
                    print(traceback.print_exc())
                    print("Exception while insert:", e)

            elif extracted_filename == "sourcereference.json":
                sr_id = file_data.get("_id")

                try:
                    data = await SourceReference_stdapi.get(sr_id)
                    if isinstance(data, dict):
                        if 'found' in data.keys() and not data['found']:
                            data = {}
                except Exception as e:
                    print(traceback.print_exc())
                    print("Exception while getting sourcereference details:", e)
                    data = {}
                try:
                    if data:
                        data_object = SourceReference_stdapi.SourceReference.parse_obj(
                            file_data
                        )
                        await data_object.update(dbName)
                    else:
                        data_object = (
                            SourceReference_stdapi.SourceReferenceCreate.parse_obj(
                                file_data
                            )
                        )
                        await data_object.create(dbName)
                    success.append(filename_no_extension)
                    if filename_no_extension in failure:
                        failure.remove(filename_no_extension)
                except Exception as e:
                    print(traceback.print_exc())
                    print("Exception while insert:", e)

            elif extracted_filename == "matchrulesumcol.json":
                print("Not inserting Match rules sum column... for now")
                continue
                unique_id = file_data.get("_id")

                try:
                    data = await MatchRuleSumColumns_stdapi.get(unique_id)
                    if isinstance(data, dict):
                        if 'found' in data.keys() and not data['found']:
                            data = {}
                except Exception as e:
                    print(traceback.print_exc())
                    print("Exception while getting matchrulesumcol details:", e)
                    data = {}
                try:
                    if data:
                        data_object = (
                            MatchRuleSumColumns_stdapi.MatchRuleSumColumns.parse_obj(
                                file_data
                            )
                        )
                        await data_object.update(dbName)
                    else:
                        data_object = (
                            MatchRuleSumColumns_stdapi.MatchRuleSumColumnsCreate.parse_obj(
                                file_data
                            )
                        )
                        await data_object.create(dbName)
                    success.append(filename_no_extension)
                    if filename_no_extension in failure:
                        failure.remove(filename_no_extension)
                except Exception as e:
                    print(traceback.print_exc())
                    print("Exception while insert:", e)

            elif extracted_filename == "matchruleref.json":
                unique_id = file_data.get("_id")

                try:
                    data = await MatchRuleReference_stdapi.get(unique_id)
                    if isinstance(data, dict):
                        if 'found' in data.keys() and not data['found']:
                            data = {}
                except Exception as e:
                    print(traceback.print_exc())
                    print("Exception while getting matchruleref details:", e)
                    data = {}
                try:
                    if data:
                        data_object = (
                            MatchRuleReference_stdapi.MatchRuleReference.parse_obj(
                                file_data
                            )
                        )
                        await data_object.update(dbName)
                    else:
                        data_object = (
                            MatchRuleReference_stdapi.MatchRuleReferenceCreate.parse_obj(
                                file_data
                            )
                        )
                        await data_object.create(dbName)
                    success.append(filename_no_extension)
                    if filename_no_extension in failure:
                        failure.remove(filename_no_extension)
                except Exception as e:
                    print(traceback.print_exc())
                    print("Exception while insert:", e)

            elif extracted_filename == "flows.json":
                unique_id = file_data.get("_id")
                dbName = framework.settings.dbName
                tableName = f"{dbName}_flows"
                flows = Flows_stdapi.Flows()
                try:
                    query = {"reconId": file_data.get('reconId')}
                    params = framework.queryparams.QueryParams()
                    params.limit = 1
                    params.q = json.dumps(query)
                    data = await flows.get_all(params, framework.settings.dbName)
                    if data.get('data',[]):
                        data = data.get('data',[])[0]
                    # print('flows data', data)
                    if isinstance(data, dict):
                        if 'data' in data.keys():
                            data = data.get('data', [])
                except Exception as e:
                    print(traceback.print_exc())
                    print("Exception while getting flows details:", e)
                    data = {}
                try:
                    if data:
                        file_data['_id'] = data['_id']
                        file_data['id'] = data['_id']
                        # print('file_data', file_data)
                        data_object = Flows_stdapi.Flows.parse_obj(file_data)
                        await data_object.update(dbName)
                    else:
                        data_object = Flows_stdapi.FlowsCreate.parse_obj(file_data)
                        await data_object.create(dbName)
                    success.append(filename_no_extension)
                    if filename_no_extension in failure:
                        failure.remove(filename_no_extension)
                except Exception as e:
                    print(traceback.print_exc())
                    print("Exception while insert:", e)

            elif extracted_filename == "feedfile.json":
                unique_id = file_data.get("_id")

                try:
                    data = await FeedFile_stdapi.get(unique_id)
                    if isinstance(data, dict):
                        if 'found' in data.keys() and not data['found']:
                            data = {}
                except Exception as e:
                    print(traceback.print_exc())
                    print("Exception while getting feeddata details:", e)
                    data = {}
                try:
                    if data:
                        data_object = FeedFile_stdapi.FeedFile.parse_obj(file_data)
                        await data_object.update(dbName)
                    else:
                        data_object = FeedFile_stdapi.FeedFileCreate.parse_obj(file_data)
                        await data_object.create(dbName)
                    success.append(filename_no_extension)
                    if filename_no_extension in failure:
                        failure.remove(filename_no_extension)
                except Exception as e:
                    print(traceback.print_exc())
                    print("Exception while insert:", e)

            elif extracted_filename == "columnDataTypes.json":
                unique_id = file_data.get("_id")

                try:
                    data = await ColumnDataTypes_stdapi.get(unique_id)
                    if isinstance(data, dict):
                        if 'found' in data.keys() and not data['found']:
                            data = {}
                except Exception as e:
                    print(traceback.print_exc())
                    print("Exception while getting column data types details:", e)
                    data = {}
                try:
                    if data:
                        data_object = ColumnDataTypes_stdapi.ColumnDataTypes.parse_obj(
                            file_data
                        )
                        await data_object.update(dbName)
                    else:
                        data_object = (
                            ColumnDataTypes_stdapi.ColumnDataTypesCreate.parse_obj(
                                file_data
                            )
                        )
                        await data_object.create(dbName)
                    success.append(filename_no_extension)
                    if filename_no_extension in failure:
                        failure.remove(filename_no_extension)
                except Exception as e:
                    print(traceback.print_exc())
                    print("Exception while insert:", e)

            elif bson.objectid.ObjectId.is_valid(filename_no_extension):
                # source json
                unique_id = file_data.get("_id")

                try:
                    data = await SourceData_stdapi.get(unique_id)
                    if isinstance(data, dict):
                        if 'found' in data.keys() and not data['found']:
                            data = {}
                except Exception as e:
                    print(traceback.print_exc())
                    print(
                        f"Exception while getting source details for source: {unique_id}\n",
                        e,
                    )
                    data = {}
                try:
                    if data:
                        data_object = SourceData_stdapi.SourceData.parse_obj(file_data)
                        await data_object.update(dbName)
                    else:
                        data_object = SourceData_stdapi.SourceDataCreate.parse_obj(
                            file_data
                        )
                        await data_object.create(dbName)
                    success.append(filename_no_extension)
                    if filename_no_extension in failure:
                        failure.remove(filename_no_extension)
                except Exception as e:
                    print(traceback.print_exc())
                    print("Exception while insert:", e)

    shutil.rmtree(extractpath)
    return {"message": "Recon Imported Successfully", "success": success, "failure": failure, "status": True}

