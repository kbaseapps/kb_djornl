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

# --- GRIN micromamba env (isolated; avoids full Anaconda) ---
USER root
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl bzip2 ca-certificates git git-lfs && \
    rm -rf /var/lib/apt/lists/*

# micromamba binary
ENV MAMBA_ROOT_PREFIX=/opt/mamba
ADD https://micro.mamba.pm/api/micromamba/linux-64/latest /tmp/mm.tar.bz2
RUN tar -xvjf /tmp/mm.tar.bz2 -C /usr/local/bin/ --strip-components=1 bin/micromamba && \
    chmod +x /usr/local/bin/micromamba && rm -f /tmp/mm.tar.bz2

# GRIN env with prebuilt R packages (no CRAN compiles)
COPY env-grin.yml /tmp/env-grin.yml
RUN /usr/local/bin/micromamba create -y -f /tmp/env-grin.yml && \
    /usr/local/bin/micromamba clean -a -y && \
    chmod -R a+rX ${MAMBA_ROOT_PREFIX}

# GRIN sources (clone inside the env so git-lfs is available)
RUN /usr/local/bin/micromamba run -n grin bash -lc '\
  git lfs install || true && \
  GIT_LFS_SKIP_SMUDGE=1 git clone --depth 1 https://github.com/sullivanka/GRIN /opt/GRIN \
'

# Extra R deps that aren’t conda-only (don’t upgrade conda pkgs)
RUN /usr/local/bin/micromamba run -n grin Rscript -e "\
  options(repos='https://cloud.r-project.org'); \
  Sys.setenv(R_REMOTES_UPGRADE='never', R_REMOTES_NO_ERRORS_FROM_WARNINGS='true'); \
  if (!requireNamespace('remotes', quietly=TRUE)) install.packages('remotes'); \
  if (!requireNamespace('RandomWalkRestartMH', quietly=TRUE)) remotes::install_github('alberto-valdeolivas/RandomWalkRestartMH', dependencies=FALSE, upgrade='never'); \
  if (!requireNamespace('KneeArrower', quietly=TRUE)) remotes::install_github('agentlans/KneeArrower', dependencies=FALSE, upgrade='never') \
"

# Built-in multiplex (required by run_grin)
COPY data/multiplex/djornl_v1_10layer.RData /kb/module/data/multiplex/djornl_v1_10layer.RData


COPY ./ /kb/module
# fix permissions
RUN chmod -R a+rw /kb/module
# build js report app
RUN mkdir -p /opt/work
RUN npm run build -- --mode production --output-path /opt/work/build
RUN make all

ENTRYPOINT [ "./scripts/entrypoint.sh" ]

CMD [ ]
