from jinja2 import Template

FIELD_PY_TEMPLATE = Template(
'''from stitches_py.resources import field, subfield

@field()
class {{ f_name }}:
    """
    {{ f_description }}
    """

    {% if not is_empty %}
    
    @subfield
    def str_sf(self) -> str:
        """
        A string subfield.
        """
        pass
    {% else %}
    pass
    {% endif %}
''')