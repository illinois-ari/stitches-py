from jinja2 import Template

HCAL_ENTRYPOINT_TEMPLATE = Template("""#!/bin/bash
echo '/tmp/core.%t.%e.%p' | tee /proc/sys/kernel/core_pattern
/opt/stitches-py/bin/{{ ss_name }}HCAL&
sleep 10000

""")