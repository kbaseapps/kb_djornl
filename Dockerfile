FROM kbase/sdkbase2:python
MAINTAINER KBase Developer
# -----------------------------------------
# In this section, you can install any system dependencies required
# to run your App.  For instance, you could place an apt-get update or
# install line here, a git checkout to download code, or run any other
# installation scripts.

# RUN apt-get update


# -----------------------------------------

RUN mkdir -p /kb/module/work
WORKDIR /kb/module
COPY ./requirements.txt /kb/module/requirements.txt
RUN pip install --extra-index-url https://pypi.anaconda.org/kbase/simple \
    -r requirements.txt

RUN apt-get update
RUN apt-get install -y graphviz
COPY ./ /kb/module
RUN chmod -R a+rw /kb/module
RUN mkdir -p /opt/work
RUN git clone \
    https://github.com/kbase/exascale_data.git \
    /opt/work/exascale_data

RUN make all

ENTRYPOINT [ "./scripts/entrypoint.sh" ]

CMD [ ]
