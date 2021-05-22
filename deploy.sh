#!/bin/bash
set -e
DEPLOY_DIR=/srv/baby-tracker
ssh $USER@$SERVER_IP "mkdir -p ${DEPLOY_DIR}"
scp requirements.txt $USER@$SERVER_IP:${DEPLOY_DIR}/
scp create-venv.sh $USER@$SERVER_IP:${DEPLOY_DIR}/
scp main.sh $USER@$SERVER_IP:${DEPLOY_DIR}/
rsync -rav -e ssh  --exclude='__pycache__' ./baby_tracker $USER@$SERVER_IP:${DEPLOY_DIR}/
ssh $USER@$SERVER_IP "apt-get install python3-venv supervisor -y"
scp supervisor.conf $USER@$SERVER_IP:/etc/supervisor/conf.d/baby-tracker.conf
ssh $USER@$SERVER_IP "cd $DEPLOY_DIR && ./create-venv.sh"
ssh $USER@$SERVER_IP "supervisorctl reread; supervisorctl update; supervisorctl restart baby_tracker"
