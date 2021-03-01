FROM kbase/sdkbase2:python
MAINTAINER KBase Developer

RUN mkdir -p /kb/module/work
WORKDIR /kb/module
# Python requirements
RUN conda update -n base -c defaults conda
COPY ./requirements.kb_sdk.txt /kb/module/requirements.kb_sdk.txt
RUN pip install -r requirements.kb_sdk.txt
COPY ./requirements.txt /kb/module/requirements.txt
RUN pip install --extra-index-url https://pypi.anaconda.org/kbase/simple \
    -r requirements.txt
# Node and node requirements
RUN curl -sL https://deb.nodesource.com/setup_14.x | bash -
RUN apt-get install -y nodejs
COPY ./package.json /kb/module/package.json
RUN NO_POSTINSTALL=true npm install --production
RUN npm install webpack-cli webpack
# Retrieve static data exascale_data
RUN git clone --depth 1 \
    https://github.com/kbase/exascale_data.git \
    /opt/work/exascale_data
# Retrieve static data relation engine
RUN git clone --depth 1 \
    https://github.com/kbase/relation_engine.git \
    /opt/work/relation_engine
# Retrieve RWR tools and data
# RUN git clone --depth 1 \
#     https://github.com/dkainer/RWRtools.git \
#     /opt/work/RWRtools
RUN mkdir -p /opt/work
COPY ./ /kb/module
RUN chmod -R a+rw /kb/module

RUN make all

ENTRYPOINT [ "./scripts/entrypoint.sh" ]

CMD [ ]
