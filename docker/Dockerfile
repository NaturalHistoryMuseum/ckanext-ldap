FROM naturalhistorymuseum/ckantest:0.1

# required by python-ldap
RUN apt-get -q -y install libldap2-dev libsasl2-dev \
    && apt-get -q clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /base/src/ckanext-ldap

# copy over the source
COPY . .

# install the base + test dependencies
RUN pip install -e .[test]

# this entrypoint ensures our service dependencies (postgresql, solr and redis) are running before
# running the cmd
ENTRYPOINT ["/bin/bash", "/opt/waits/basic.sh"]

# run the tests with coverage output
CMD ["bash", "docker/run-tests.sh"]
