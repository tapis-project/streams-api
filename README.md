Tapis Streams API

This API requires the tapis python-sdk so clone down the latest into a tapy folder
```
git clone https://github.com/tapis-project/python-sdk.git tapy
```

You will need to have the Nginx proxy service docker container running locally to route traffic for the tapipy to work.
Update the dev.conf in the nginx folder to use your local machines IP addres - NOTE localhost will not work since this will be inside a container and needs to route from the container to the host. From the nginx folder and run the docker-compose command. 
```
cd nginx
docker-compose up -d
```

Then run docker-compose to bring up the Streams API local dependencise (chords, mysql, influxdb)
```
docker-compose up -d
```

Next update the config-local.json with your local IP for accessing dependencies (i.e chords, influxdb, mysql etc) Now you can start to build the streams-api docker container locally.
```
docker build -t tapis/streams-api:latest .
```

Now you can run the streams API server locally:
```
docker run -p 5000:5000 tapis/streams-api:latest
```

You can then go to localhost:5000/v3/streams/etc. Or access it via tapipy.  Note that for tapipy to route to your local Streams API you need to modify the Tapis client after you have authenticated and create a token with the client you need to update the client.base_url value to be your "http://your-local-ip:5001" - once that is set streams calls made with tapipy for the client session will route to your local Streams API.


## Running tests
1.) Before you start running the tests you will need to add the following to the config-local.json file for the tests with working username & password for the tenant you are testing against for the other services(sk,meta,abaco etc)
 ```
     "test_tenant_id" : "dev",
     "test_username" :"testusername",
     "test_password" :"testpassword"
 ```
2.) Build the tapis/streams-api docker container:  
```
docker build -t tapis/streams-api:latest .
```
3.) Build the test docker image:
```
docker build -t tapis/streams-tests -f Dockerfile-tests .
```
4.) Run these tests using the built docker image:
```
docker run -it --rm --name=streams-test -p 5000:5000 tapis/streams-tests
```
