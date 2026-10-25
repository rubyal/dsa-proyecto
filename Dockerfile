FROM python:3.12-slim

ARG HOST_UID=1000
ARG HOST_GID=1000

RUN apt-get update \
    && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

# Usuario con tu mismo UID/GID: los archivos que cree el contenedor no quedan como root
RUN groupadd -g ${HOST_GID} jovyan \
    && useradd -m -u ${HOST_UID} -g ${HOST_GID} jovyan

COPY requirements.txt /tmp/requirements-jupyter.txt
RUN pip install --no-cache-dir -r /tmp/requirements-jupyter.txt

USER jovyan
WORKDIR /work
EXPOSE 8888

CMD ["jupyter", "lab", "--ip=0.0.0.0", "--port=8888", "--no-browser"]