# GeoGeekSuite

The ***GeoGeekSuite*** is a collection of ***Open Source*** tools, that are useful to manage ***geospatial*** data.
These tools are ochestrated with ***Kubernetes*** and easy to deploy with ***Ansible***.

Main components are:

- PostGIS for data storage
- GDAL and osm2pgsql to import data to the database
- A Job server that manages execution of different tasks (e.g. the import with the tools mentioned above)
- PgAdmin for data exploration and geospatial operations executed directly on the database
- Jupyter Notebook for scriting and data access
- Elasticsearch and Kibana for centralised logging
- High level python wrappers to facilitate common processes

Jupyter Notebooks are provided to illustrate the data handling for different example scenarios.

## Status

*** work in progress ***





