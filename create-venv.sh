#!/bin/bash
function prepend() { while read line; do echo "${1}${line}"; done; }
python3 -m venv .venv
requirements_args=$(ls requirements.* | prepend "-r ")
echo "requirements found:
${requirements_args}"
.venv/bin/pip install $requirements_args
