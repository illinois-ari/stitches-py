ARG IMAGE_REGISTRY=localhost:5000
FROM ${IMAGE_REGISTRY}/stitches-py-dev

COPY --chown=sosite:sosite src/stitches-py /tmp/stitches-py
USER root
RUN pip3 install -t /opt/stitches-py/lib /tmp/stitches-py
