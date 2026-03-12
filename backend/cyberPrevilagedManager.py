import framework
import sys
import json
import time
import redis
import Helpers
import datetime


class RedisQueue(object):
    """Simple Queue with Redis Backend"""
    def __init__(self, name, namespace='queue', **redis_kwargs):
        """The default connection parameters are: host='localhost', port=6379, db=0"""
        self.__db = redis.Redis(**redis_kwargs)
        self.key = '%s:%s' % (namespace, name)

    def qsize(self):
        """Return the approximate size of the queue."""
        return self.__db.llen(self.key)

    def empty(self):
        """Return True if the queue is empty, False otherwise."""
        return self.qsize() == 0

    def put(self, item):
        """Put item into the queue."""
        self.__db.rpush(self.key, item)

    def get(self, block=True, timeout=None):
        """Remove and return an item from the queue.

        If optional args block is true and timeout is None (the default), block
        if necessary until an item is available."""
        if block:
            item = self.__db.blpop(self.key, timeout=timeout)
        else:
            item = self.__db.lpop(self.key)

        if item:
            item = item[1]
        return item

    def get_nowait(self):
        """Equivalent to get(False)."""
        return self.get(False)


class CyberPrevillagedService():
    def runSystemdScripts(self, scriptName, arguments, serviceaction='start'):
        cmd = f"systemctl {serviceaction} {scriptName}.service"
        if len(arguments) > 0:
            cmd = f'systemctl {serviceaction} {scriptName}@"{" ".join(arguments)}".service'
        Helpers.execute(cmd)



def run():
    queue_ins = RedisQueue("previlegedservices")
    while True:
        try:
            # if ins.empty():
            #     time.sleep(30)
            #     continue
            resp = queue_ins.get(timeout=120)
            if not resp:
                time.sleep(10)
                continue
            print("MSG Recieved %s" % resp)
            msg = json.loads(resp)
            if msg.get('model') == "service":
                if not msg.get('serviceName'):
                    print("Only systemd service changes will be allowed")
                    continue
                CyberPrevillagedService().runSystemdScripts(msg["serviceName"], msg["arguments"], msg.get('serviceaction', 'start'))
                time.sleep(5)
        except Exception as e:
            print("Exception in processing previleged queue %s" % e)
            time.sleep(30)


if __name__ == "__main__":
    if len(sys.argv) == 1:
        run()
    if sys.argv[1] == "installUpdates":
        print("*************** Code Update Started At %s ***************" % datetime.datetime.utcnow().isoformat())
        installUpdates(inputargs="".join(sys.argv[2:]))
        print("*************** Code Update Completed At %s ***************" % datetime.datetime.utcnow().isoformat())

