from jinja2 import Template

SSI_DOCKERFILE_TEMPLATE = Template("""
FROM {{ image_registry }}/stitches-py-dev as builder
WORKDIR /opt/stitches-py
COPY . .
USER root
RUN cmake . && make && \
    cp -r inputs/ /opt/stitches-py/lib/ && \
    cp bin/*.so /opt/stitches-py/lib/ && \
    sudo chmod +x /opt/stitches-py/bin/{{ ss_name }}

ENV PYTHONPATH=$PYTHONPATH:/opt/stitches-py/inputs:/opt/stitches-py/lib
ENV PATH=$PATH:/opt/stitches-py/bin

FROM {{ image_registry }}/{{ wrapper_image }}
USER root
COPY --from=builder /opt/stitches-py /opt/stitches-py

ENV PYTHONPATH=$PYTHONPATH:/opt/stitches-py/inputs:/opt/stitches-py/lib
ENV PATH=$PATH:/opt/stitches-py/bin
COPY entrypoint.sh /opt/stitches-py/entrypoint.sh
RUN chmod +x /opt/stitches-py/entrypoint.sh
ENTRYPOINT ["/opt/stitches-py/entrypoint.sh"]

""")