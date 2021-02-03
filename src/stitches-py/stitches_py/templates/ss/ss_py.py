from jinja2 import Template

SSI_PY_TEMPLATE = Template('''
import asyncio
from stitches_py.resources import field, subfield, subsystem, ss_interface, ss_thread

@subsystem()
class {{ to_camel(ss_name) }}:
    """
    {{ ss_description }}
    """
    {% if is_empty %}
    pass
    {% else %}
    pass
    {% endif %}

''')