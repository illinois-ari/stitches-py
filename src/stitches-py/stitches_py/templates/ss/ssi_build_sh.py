from jinja2 import Template

SSI_BUILD_SH_TEMPLATE = Template("""
#!/bin/bash

OS=`uname -s`
ARCH=`uname -m`

cmake .
make
""")