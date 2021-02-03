from jinja2 import Template

SSI_TEST_TEMPLATE = Template("""
from cball_stitches.ssi.{{r._CBALL_MODULE}}.{{r._CBALL_TYPE_NAME}} import {{r._CBALL_TYPE_NAME}}SSIUpper

class MockCore:
    {%- for m in r_spec.methods %}
    def {{ m.name }}(self):
        pass
    {% endfor %}

    {%- for e in r_spec.events %}
    def {{ e.name }}(self):
        pass
    {% endfor %}

def test_{{r._CBALL_TYPE_NAME}}_init():
    ssi = {{r._CBALL_TYPE_NAME}}SSIUpper(MockCore())
    ssi.init()

""")