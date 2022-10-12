FROM naturalhistorymuseum/ckantest:0.1

# these two are required by ckanext-ldap
RUN apt-get -q -y install libldap2-dev libsasl2-dev \
    && apt-get -q clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /base/src/ckanext-ldap

# copy over the ckanext-ldap source
COPY . .

# install the dependencies
RUN python setup.py develop && \
    pip install -r requirements.txt && \
    pip install -r dev_requirements.txt

# this entrypoint ensures our service dependencies (postgresql, solr and redis) are running before
# running the cmd
ENTRYPOINT ["/bin/bash", "/opt/waits/basic.sh"]

# run the tests with coverage output
CMD ["pytest", "--cov=ckanext.ldap", "--ckan-ini=test.ini", "tests"]
