#!/bin/bash

export FLASK_APP=superset
export FLASK_RUN_HOST='smartrecon.com'
source /data/ngerecon/superset/bin/activate
superset run -h 0.0.0.0 -p 8088 --with-threads --reload --debugger >> /var/log/smartrecon/superset.log
