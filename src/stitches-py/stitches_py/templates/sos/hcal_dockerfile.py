from jinja2 import Template

HCAL_DOCKERFILE_TEMPLATE = Template("""
FROM {{ image_registry }}/stitches-py-dev as builder
COPY . /opt/stitches-py/build
WORKDIR /opt/stitches-py/build
USER root
RUN uname -a
RUN cmake . && make && \
    mkdir -p /opt/stitches-py/bin && \
    cp bin/{{ ss_name }}HCAL /opt/stitches-py/bin/{{ ss_name }}HCAL
COPY entrypoint.sh /opt/stitches-py/entrypoint.sh
RUN chmod +x /opt/stitches-py/entrypoint.sh
ENTRYPOINT ["/opt/stitches-py/entrypoint.sh"]
""")