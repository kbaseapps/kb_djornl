FROM kbase/sdkbase2:python
MAINTAINER KBase developer

RUN apt-get update
RUN apt-get upgrade -y
RUN mkdir -p /kb/module/work
WORKDIR /kb/module
# Python and R requirements
ENV PIP_PROGRESS_BAR=off
RUN conda update -n base -c defaults conda
COPY ./scripts/rwrtools-env-create.sh /kb/module/scripts/rwrtools-env-create.sh
RUN ./scripts/rwrtools-env-create.sh
COPY ./requirements.kb_sdk.txt /kb/module/requirements.kb_sdk.txt
RUN pip install -r requirements.kb_sdk.txt
COPY ./requirements.txt /kb/module/requirements.txt
RUN pip install --extra-index-url https://pypi.anaconda.org/kbase/simple \
    -r requirements.txt
# Node and node requirements
RUN curl -fsSL https://deb.nodesource.com/setup_14.x | bash -
RUN apt-get install -y nodejs
COPY ./package.json /kb/module/package.json
RUN NO_POSTINSTALL=true npm install --production
RUN npm install webpack-cli webpack
COPY ./ /kb/module
# fix permissions
RUN chmod -R a+rw /kb/module
# build js report app
RUN mkdir -p /opt/work
RUN npm run build -- --mode production --output-path /opt/work/build
RUN make all

ENTRYPOINT [ "./scripts/entrypoint.sh" ]

CMD [ ]
