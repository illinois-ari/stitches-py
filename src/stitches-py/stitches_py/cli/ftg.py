import click
import os
import signal
import json
from tabulate import tabulate
import sys

from stitches_py.resources import Field
from stitches_py.resources.ftg import FTGRepoClient
from stitches_py.resources.ftg.templates import FIELD_PY_TEMPLATE
from stitches_py import utils

@click.group('ftg', help='FTG commands')
@click.pass_context
def FTGCLIGroup(ctx):
    pass

@FTGCLIGroup.command('list-fields', help='List Fields')
@click.pass_context
def list_fields(ctx):
    r_dict = utils.resources_in_path(ctx.obj['input_dir'], include_filter=Field)

    headers = ["ID", "Description"]
    click.echo(tabulate([(k,) + (v._RESOURCE_DESCRIPTION,) for k,v in r_dict.items()], headers=headers))


@FTGCLIGroup.command('register', help='Register Fields')
@click.pass_context
def register_fields(ctx):
    r_dict = utils.resources_in_path(ctx.obj['input_dir'], include_filter=Field)
    client = FTGRepoClient()

    for f in r_dict.values():
        client.register_field(f)

    

@click.option('--empty', type=bool, help="Don't populate example subfields.", is_flag=True)
@click.option('--out-dir', type=click.Path(exists=True), required=False, default='inputs')
@click.option('--description', type=str, required=False)
@click.argument('NAME', type=str)
@FTGCLIGroup.command('create-field', help='Create a new Field')
@click.pass_context
def create(ctx, name, out_dir, description, empty):
    utils.template_to_path(
        FIELD_PY_TEMPLATE,
        os.path.join(out_dir, f'{name}.py'),
        **{
            'f_name': name,
            'f_description': description or name,
            'to_camel': utils.to_camel,
            'is_empty': empty
        }
    )
