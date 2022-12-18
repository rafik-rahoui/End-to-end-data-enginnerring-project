 #! /bin/bash
sleep 20
sudo chown -R 1001 /var/run/docker.sock
~/bin/docker-compose build
~/bin/docker-compose up -d
docker ps