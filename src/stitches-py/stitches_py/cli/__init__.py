import click
import pkg_resources
import logging
import sys

from .cluster import ClusterCLIGroup
from .ftg import FTGCLIGroup
from .sos import SoSCLIGroup
from .ss import SSCLIGroup

@click.option('--input-dir', type=click.Path(exists=True), required=False, default='/opt/stitches-py/inputs')
@click.group()
@click.pass_context
def cli_group(ctx, input_dir):
    sys.path.insert(0, input_dir)
    ctx.ensure_object(dict)
    ctx.obj['input_dir'] = input_dir


cli_group.add_command(ClusterCLIGroup)
cli_group.add_command(FTGCLIGroup)
cli_group.add_command(SoSCLIGroup)
cli_group.add_command(SSCLIGroup)

