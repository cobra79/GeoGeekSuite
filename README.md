# GeoGeekSuite
Integrated collection of geospatial tools running in Kubernetes

## Objectives
 
- Setup a suite state of the art open sources of components for processing and storage of geospatial information
- Create high level wrappers for common / frequently used processes
- Provide examples for different workflows
- Run it locally or in the cloud
- Easy to install with an automated deployment

## Status

*** Everything work in progress ***

## Technology choice

Initial draft:

- Geospatial Database: PostGIS
- Database Access: Via UI using PgAdmin or scripting
- Scripting Language: Python 3.x
- Scripting Environment: Jupyter Notebook
- Publishing Geoinformation: Geoserver
- Automation: Ansible
- Logging: Probably ELK stack

## Setup

### Prerequisites

- Docker & Kubernetes (currently testing with Docker Desktop on a Mac with K8S 1.19.8)
- Ansible

### Installation

- Clone this repo.
- Create an inventory.yaml file (copy inventory-sample.yaml and update parameters)
- Create an environment.yaml file (copy environment-sample.yaml and update parameters)
- Create an credentials.yaml file (copy credentials-sample.yaml and update parameters)
- Update main.yaml if necessary (e.g. update hosts)
- Run the Ansible Workbook for the installation
'''
ansible-workbook main.yaml
'''
- Access applications via the browser

## Project components / Ansible roles

### Kube

Helper role to setup common Kubernetes resources (e.g. create a namespace)


