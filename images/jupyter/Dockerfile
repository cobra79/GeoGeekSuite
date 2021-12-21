FROM jupyter/base-notebook:notebook-6.4.6

USER root

RUN apt-get update \
    && apt-get install -yq --no-install-recommends \
        apt-utils \
        curl \
        pkg-config \
        software-properties-common \
    && LANG=C.UTF-8 add-apt-repository -y ppa:ubuntugis/ppa \
    && apt update \
    && apt install gdal-bin -y \
    && apt install unzip -y \
    && apt install osm2pgsql -y

USER jovyan
RUN pip3 install ipyleaflet && \
 conda install psycopg2 && \
 pip3 install pandas