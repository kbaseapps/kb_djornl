FROM kbase/sdkbase2:python
MAINTAINER KBase Developer

RUN mkdir -p /kb/module/work
WORKDIR /kb/module
# Python requirements
COPY ./requirements.txt /kb/module/requirements.txt
RUN pip install --extra-index-url https://pypi.anaconda.org/kbase/simple \
    -r requirements.txt
# Node and node requirements
RUN curl -sL https://deb.nodesource.com/setup_14.x | bash -
RUN apt-get install -y nodejs
COPY ./package.json /kb/module/package.json
RUN NO_POSTINSTALL=true npm install --production
RUN npm install webpack-cli webpack
# Retrieve static data
RUN git clone \
    https://github.com/kbase/exascale_data.git \
    /opt/work/exascale_data
COPY ./ /kb/module
RUN chmod -R a+rw /kb/module
RUN mkdir -p /opt/work

RUN make all

ENTRYPOINT [ "./scripts/entrypoint.sh" ]

CMD [ ]
