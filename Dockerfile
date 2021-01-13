FROM kbase/sdkbase2:python
MAINTAINER KBase Developer

RUN apt-get update
RUN apt-get install -y graphviz

RUN mkdir -p /kb/module/work
WORKDIR /kb/module
COPY ./requirements.txt /kb/module/requirements.txt
RUN pip install --extra-index-url https://pypi.anaconda.org/kbase/simple \
    -r requirements.txt

COPY ./ /kb/module
RUN chmod -R a+rw /kb/module
RUN mkdir -p /opt/work
RUN git clone \
    https://github.com/kbase/exascale_data.git \
    /opt/work/exascale_data

RUN make all

ENTRYPOINT [ "./scripts/entrypoint.sh" ]

CMD [ ]
