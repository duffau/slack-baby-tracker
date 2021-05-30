#!/bin/bash
set -e
QUICK=0
DEPLOY_DIR=/srv/baby-tracker

usage()
{
    echo "usage: ./deploy.sh [-q|--quick]"
}

deploy()
{
    ssh $USER@$REMOTE_HOST "mkdir -p ${DEPLOY_DIR}"
    scp requirements.txt $USER@$REMOTE_HOST:${DEPLOY_DIR}/
    scp main.sh $USER@$REMOTE_HOST:${DEPLOY_DIR}/
    rsync -rav -e ssh  --exclude='__pycache__' ./baby_tracker $USER@$REMOTE_HOST:${DEPLOY_DIR}/
    scp supervisor.conf $USER@$REMOTE_HOST:/etc/supervisor/conf.d/baby-tracker.conf
    scp create-venv.sh $USER@$REMOTE_HOST:${DEPLOY_DIR}/
    if [ $QUICK == 0 ]
    then
        ssh $USER@$REMOTE_HOST "apt-get update && apt-get install python3-venv supervisor sqlite3 -y"
        ssh $USER@$REMOTE_HOST "cd $DEPLOY_DIR && ./create-venv.sh"
        # Import database from CSV's
        rsync -rav -e ssh  --exclude='__pycache__' ./data $USER@$REMOTE_HOST:${DEPLOY_DIR}/
        ssh $USER@$REMOTE_HOST "cd $DEPLOY_DIR && ./data/import.sh"
        setup_backups
    fi
    ssh $USER@$REMOTE_HOST "supervisorctl reread; supervisorctl update; supervisorctl restart baby_tracker"
}


setup_backups()
{
    ssh $USER@$REMOTE_HOST "mkdir -p ${DEPLOY_DIR}/backup"
    cron_schedule='0 4 \* \* \*'
    backup_cmd="cp ${DEPLOY_DIR}/db.sqlite ${DEPLOY_DIR}/backup/db-\$(date +%Y-%m-%d).sqlite; find ${DEPLOY_DIR}/backup/ -type f -mtime +10 -delete"
    crontab_line="$cron_schedule $backup_cmd"
    echo "crontab_line: $crontab_line"
    ssh $USER@$REMOTE_HOST "echo $crontab_line | crontab -"
}

while [ "$1" != "" ]; do
    case $1 in
        -q | --quick )
                                  QUICK=1;;
        -h | --help )             usage
                                  exit
                                  ;;
        * )                       usage
                                  exit 1
    esac
    shift
done
deploy