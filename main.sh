#!/bin/bash
trap "trap - SIGTERM && kill -- -$$" SIGINT SIGTERM EXIT
export FLASK_APP=baby_tracker/serve.py
export FLASK_ENV=development
export PYTHONUNBUFFERED=TRUE
.venv/bin/flask run -p ${SERVER_PORT:-80} -h ${SERVER_IP:-0.0.0.0}
