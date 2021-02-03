from jinja2 import Template

BUILDX_TOML_TEMPLATE = Template("""
[registry."{{ image_registry }}"]
  http = true
  insecure = true
""")