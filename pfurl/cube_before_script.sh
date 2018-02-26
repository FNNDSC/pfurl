#!/bin/bash
set -ev
cd ..
#make this one of your repos and modify it to install pfurl!
git clone https://github.com/FNNDSC/ChRIS_ultron_backEnd.git
pushd pfurl/
docker build -t fnndsc/pfurl:latest .
popd
pushd ChRIS_ultron_backEnd/
docker build -t fnndsc/chris_dev_backend .
export STOREBASE=$(pwd)/FS/remote
docker-compose up -d
docker-compose exec chris_dev_db sh -c 'while ! mysqladmin -uroot -prootp status 2> /dev/null; do sleep 5; done;'
docker-compose exec chris_dev_db mysql -uroot -prootp -e 'GRANT ALL PRIVILEGES ON *.* TO "chris"@"%"'
docker-compose exec chris_dev python manage.py migrate
docker swarm init --advertise-addr 127.0.0.1