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
