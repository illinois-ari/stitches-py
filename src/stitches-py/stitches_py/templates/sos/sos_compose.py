from jinja2 import Template

SOS_COMPOSE_TEMPLATE = Template("""---
version: "3"
services:
{% for ss_name, ss in ss_map.items() %}
  {{ ss_name }}:
    image: {{ image_registry }}/{{ ss.ss_cls._RESOURCE_NAME.lower() }}
    user: root
    privileged: true
    working_dir: /opt/stitches-py/bin
    deploy:
      placement:
        constraints:
          - "node.hostname=={{ ss_node_map[ss_name] }}"
{% if ss.gpu_enabled %}
      resources:
        reservations:
          devices:
            - capabilities:
              - gpu
{% endif %}
    volumes:
      - {{ ss_name }}-ipc:/opt/stitches-py/bin/ipc
      - {{ ss_name }}-namedpipes:/opt/stitches-py/bin/namedpipes
{% for v in ss.extra_volumes %}
      - {{ v }}
{% endfor %}
    networks:
      default:
        ipv4_address: {{ ss_ip_map[ss_name] + 1 }}
    ulimits:
        core: -1
    devices: {{ ss.devices | tojson }}
  {{ ss_name }}-hcal:
    image: {{ image_registry }}/{{ ss_name }}-hcal
    user: root
    privileged: true
    working_dir: /opt/stitches-py/bin
    deploy:
      placement:
        constraints:
          - "node.hostname=={{ ss_node_map[ss_name] }}"
    volumes:
      - {{ ss_name }}-ipc:/opt/stitches-py/bin/ipc
      - {{ ss_name }}-namedpipes:/opt/stitches-py/bin/namedpipes
    networks:
      default:
        ipv4_address: {{ ss_ip_map[ss_name] }}
    ulimits:
        core: -1
{% endfor %}
volumes:
{% for ss_name, ss in ss_map.items() %}
  {{ ss_name }}-ipc:
  {{ ss_name }}-namedpipes:
{% endfor %}
networks:
  default:
    ipam:
     config:
       - subnet: {{ subnet_cidr }}
""")