# inherit from the flaskbase
FROM tapis/flaskbase

# set the name of the api, for use by
ENV TAPIS_API streams

# install additional requirements for the service
COPY requirements.txt /home/tapis/requirements.txt
RUN pip install -r /home/tapis/requirements.txt

# copy service source code
COPY configschema.json /home/tapis/configschema.json
COPY config-local.json /home/tapis/config.json
COPY service /home/tapis/service

# run service as non-root tapis user
RUN chown -R tapis:tapis /home/tapis
USER tapis
