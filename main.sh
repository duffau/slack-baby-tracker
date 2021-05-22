#!/bin/bash
trap "trap - SIGTERM && kill -- -$$" SIGINT SIGTERM EXIT
export FLASK_APP=baby_tracker/serve.py
.venv/bin/flask run -p 80 -h 0.0.0.0
