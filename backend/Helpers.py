import asyncio
import socket
import datetime
import subprocess
from pkg_resources import parse_version


def execute(command, wait_for_completion=True):
    child = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                             close_fds=True)
    if wait_for_completion:
        out, err = child.communicate()
        status = child.returncode
        return status, out, err
    else:
        return child


async def asyncioExecute(cmd):
    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE)

    stdout, stderr = await proc.communicate()
    if stdout:
        stdout = stdout.decode()
    if stderr:
        stderr = stderr.decode()
    return proc.returncode, stdout, stderr


def version_compare(compare, reference):
    """ Generic Version Comparator Utility """
    compare = str(compare).lower()
    reference = str(reference).lower()
    vals = compare.split(".")
    ref = reference.split(".")
    index = 0
    for val in vals:
        if len(ref) > index + 1:
            cmp_val = ref[index]
            if not (cmp_val.isdigit() and val.isdigit()):
                size_diff = len(cmp_val) - len(val)
                if size_diff > 0:
                    for i in range(0, size_diff):
                        val = val + "0"
                    vals[index] = val
                else:
                    for i in range(0, size_diff):
                        cmp_val = cmp_val + "0"
                    ref[index] = cmp_val
            elif cmp_val.isdigit() and val.isdigit():
                ref[index] = cmp_val
            else:
                size_diff = len(cmp_val) - len(val)
                if size_diff > 0:
                    for i in range(0, size_diff):
                        val = "0" + val
                    vals[index] = val
                else:
                    for i in range(0, size_diff):
                        cmp_val = "0" + cmp_val
                    ref[index] = cmp_val
    value = ".".join(vals)
    reference = ".".join(ref)
    if parse_version(value) > parse_version(reference):
        return ">"
    elif parse_version(value) < parse_version(reference):
        return "<"
    else:
        return "="


# Query Builder For Elastic Search Queries
def buildElsQuery(must=None, should=None, must_not=None, mustExpression=None, mustNotExpression=None,
                  shouldExpression=None):
    query = {"query": {"bool": {}}}
    if must:
        query["query"]["bool"]["must"] = [{"match": {key: value}} for key, value in must.items()]
    if mustExpression:
        if not isinstance(mustExpression, list):
            mustExpression = [mustExpression]
        for exp in mustExpression:
            if "must" not in query["query"]["bool"]:
                query["query"]["bool"]["must"] = []
            query["query"]["bool"]["must"].extend([{key: value} for key, value in exp.items()])
    if should:
        shouldQuery = []
        for key, value in should.items():
            shouldQuery.extend([{"match": {key: v}} for v in value])
        if shouldExpression:
            shouldQuery.extend([{key: value} for key, value in shouldExpression.items()])
        if shouldQuery:
            if must:
                query["query"]["bool"]["must"].append({"bool": {"should": shouldQuery}})
            else:
                query["query"]["bool"]["should"] = shouldQuery
    elif shouldExpression:
        shouldQuery = []
        # shouldQuery = [{key: value} for key, value in shouldExpression.items()]
        if shouldExpression:
            if not isinstance(shouldExpression, list):
                shouldExpression = [shouldExpression]
            for exp in shouldExpression:
                shouldQuery.extend([{key: value} for key, value in exp.items()])
        if shouldQuery:
            if must:
                query["query"]["bool"]["must"].append({"bool": {"should": shouldQuery}})
            else:
                query["query"]["bool"]["should"] = shouldQuery
    if must_not:
        query["query"]["bool"]["must_not"] = [{"match": {key: value}} for key, value in must_not.items()]
    if mustNotExpression:
        if not query["query"]["bool"].get("must_not"):
            query["query"]["bool"]["must_not"] = []
        if not isinstance(mustNotExpression, list):
            mustNotExpression = [mustNotExpression]
        for exp in mustNotExpression:
            query["query"]["bool"]["must_not"].extend([{key: value} for key, value in exp.items()])
    return query

def gethostname(hostname):
    try:
        host = socket.gethostbyname(hostname)
        return True, host
    except socket.error:
        return False, "Error connecting to domain %s" % hostname
    except Exception as e:
        return False, "Error connecting to domain %s" % hostname


# Convert the data-type of the values based on the schema defined.
def cast_datatype(doc=None, schema=None):
    if not doc:
        doc = {}

    if not schema:
        schema = {}

    tmp = {}
    for key, value in doc.items():
        if key not in schema:
            continue
        if isinstance(value, eval(schema[key]['type'])):
            if schema[key].get('convert') == 'datetime':
                try:
                    value = datetime.datetime.strptime(value, '%d-%m-%Y %H:%M:%S')
                except ValueError:
                    continue
            tmp[key] = value
        elif schema[key].get('default') is not None:
            tmp[key] = schema[key]['default']

    return tmp

