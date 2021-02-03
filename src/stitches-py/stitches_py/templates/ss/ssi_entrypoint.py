from jinja2 import Template

SSI_ENTRYPOINT_TEMPLATE = Template("""#!/bin/bash
echo '/tmp/core.%e.%p' | tee /proc/sys/kernel/core_pattern
/opt/stitches-py/bin/{{ ss_name }}&
sleep 10000
""")