#!/bin/bash

HERE=$(pwd)

sudo git clone --branch=2.8 https://github.com/ckan/ckan /ckan
sudo chmod -R a+rw /ckan

wget http://archive.apache.org/dist/lucene/solr/5.5.4/solr-5.5.4.tgz -O /tmp/solr.tgz
sudo mkdir /solr
sudo tar xzf /tmp/solr.tgz -C /solr
sudo /solr/solr-5.5.4/bin/solr start
sudo /solr/solr-5.5.4/bin/solr create_core -c ckan
sudo cp /ckan/ckan/config/solr/schema.xml /solr/solr-5.5.4/server/solr/ckan/conf/
sudo wget -O /solr/solr-5.5.4/server/solr/ckan/conf/solrconfig.xml $SOLR_CONFIG_URL
sudo /solr/solr-5.5.4/bin/solr restart

cd /ckan
pip install --upgrade pip
pip install -r requirement-setuptools.txt
pip install -r requirements.txt
pip install -r dev-requirements.txt
python setup.py develop

sudo -u postgres psql -c "CREATE USER ckan_default WITH PASSWORD 'pass';"
sudo -u postgres psql -c 'CREATE DATABASE ckan_test WITH OWNER ckan_default;'

sudo -u postgres psql -c "CREATE USER datastore_default WITH PASSWORD 'pass';"
sudo -u postgres psql -c 'CREATE DATABASE datastore_test WITH OWNER ckan_default;'

paster db init -c /ckan/test-core.ini
paster datastore set-permissions -c test-core.ini | sudo -u postgres psql

cd $HERE
pip install -r requirements.txt
pip install -r dev_requirements.txt
pip install -e .
