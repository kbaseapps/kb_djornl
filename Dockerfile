FROM kbase/sdkpython:3.8.0
MAINTAINER Dakota Blair
LABEL org.opencontainers.image.authors="David Dakota Blair <dblair@bnl.gov>"

RUN apt-get update
RUN apt-get upgrade -y
RUN mkdir -p /kb/module/work
WORKDIR /kb/module
# Python and R requirements
ENV PIP_PROGRESS_BAR=off
ENV PATH=$PATH:/opt/conda3/bin
RUN sh /opt/conda3/etc/profile.d/conda.sh
RUN conda update -n base -c defaults conda
COPY ./scripts/rwrtools-env-create.sh /kb/module/scripts/rwrtools-env-create.sh
RUN ./scripts/rwrtools-env-create.sh
COPY ./requirements.kb_sdk.txt /kb/module/requirements.kb_sdk.txt
RUN conda install pip
RUN pip install -r requirements.kb_sdk.txt
COPY ./requirements.txt /kb/module/requirements.txt
RUN pip install --extra-index-url https://pypi.anaconda.org/kbase/simple \
    -r requirements.txt
# Node and node requirements
RUN curl -SLO https://deb.nodesource.com/nsolid_setup_deb.sh
RUN chmod 500 nsolid_setup_deb.sh
RUN ./nsolid_setup_deb.sh 20
RUN apt-get install -y nodejs
COPY ./package.json /kb/module/package.json
COPY ./scripts/postinstall.py /kb/module/scripts/postinstall.py
RUN NO_POSTINSTALL=true npm install --omit=dev
RUN npm install webpack-cli webpack

# Built-in multiplex (required by run_grin)
#COPY data/multiplex/djornl_v1_10layer.RData /kb/module/data/multiplex/djornl_v1_10layer.RData


COPY ./ /kb/module
# fix permissions
RUN chmod -R a+rw /kb/module
RUN git clone https://github.com/sullivanka/GRIN.git
RUN bash -lc "source activate rwrtools && R -q -e \"install.packages(c('signal', 'KneeArrower'), repos='https://cloud.r-project.org')\"" 


# build js report app
RUN mkdir -p /opt/work
RUN npm run build -- --mode production --output-path /opt/work/build
RUN make all

ENTRYPOINT [ "./scripts/entrypoint.sh" ]

CMD [ ]
