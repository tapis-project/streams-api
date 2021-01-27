Tapis Streams API

This API requires the tapis python-sdk so clone down the latest into a tapy folder
```
git clone https://github.com/tapis-project/python-sdk.git tapy
```

Know you can start to build the streams-api docker container locally.
```
docker build -t tapis/streams-api:latest .
```

Then run docker-compose
```
docker-compose up -d
```

Or to just test the API without dependencies:
```
docker run -p 5000:5000 tapis/streams-api:latest
```

You can then go to localhost:5000/v3/streams/etc.


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
