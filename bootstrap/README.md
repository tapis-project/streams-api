#Bootstrap Streams Service
The scripts in this folder should be used to create necessary Meta database tables for a streams service to function in a Tapis deployment.

##Build a Docker Container
```
docker build -t tapis/streamsboostrap:lastest -f Dockerfile-boostrap .S
```

##Run the container to bootstrap
```
docker run -it tapis/streamsbootstap:latest -env 'TAPIS_BASEURL=https://dev.develop.tapis.io' \
> -env STREAMS_USER='streams' \
> -env STREAMS_SERVICE_PASSWORD='streamsfsdfsdfsdfsdfsdfsdfsdf' \
> -env META_SERVICE_PASSWORD='metasdfdfsdfsdfsdfsdfsdfsdf' \
> -env STREAMS_DB='TENANT_DB'
```

You must set 5 environment variables.

* TAPIS_BASEURL is the base url for the tapis tenant you will be bootstrapping the streams service for.
* STREAMS_USER this should nearly always be 'streams'
* STREAMS_SERVICE_PASSWORD the password in SK for the Tapis Streams service 'streams' username for the tenant specificed by the TAPIS_BASEURL
* META_SERVICE_PASSORD the password for the Tapis Meta service user  for the tenant specificed by the TAPIS_BASEURL
* STREAMS_DB the database name in the Meta service that will be updated with new tables
