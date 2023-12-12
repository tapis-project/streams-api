#!/bin/bash
docker stop streamsapi && docker build -t tapis/streams-api:latest . && docker rm streamsapi && docker run -p 5000:5000 --name=streamsapi tapis/streams-api:latest