#!/bin/bash
imageName=vueservation-backend-app
containerName=dockservation-backend

sudo docker build -t $imageName .

echo Delete old container...
sudo docker rm -f $containerName

echo Run new container...
sudo docker run -it -p 8000:8000 --rm --name $containerName $imageName
