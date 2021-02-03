import asyncio
import click
import os
import signal
import json
from tabulate import tabulate
import sys
import types

from stitches_py.resources import Subsystem
from stitches_py import utils
from stitches_py.templates.ss import SSI_PY_TEMPLATE


@click.group('ss', help='Subsystem commands')
@click.pass_context
def SSCLIGroup(ctx):
    pass

@SSCLIGroup.command('list', help='List Subsystems')
@click.pass_context
def list_ss(ctx):
    r_dict = utils.resources_in_path(ctx.obj['input_dir'], include_filter=Subsystem)
    headers = ["ID", "Description"]
    click.echo(tabulate([(k,) + (v._RESOURCE_DESCRIPTION,) for k,v in r_dict.items()], headers=headers))



@click.option('--build-dir', type=click.Path(exists=True), required=False, default='build')
@click.option('--dev-img', type=str, required=False, default='localhost:5000/stitches-dev:dev')
@click.argument('ss', nargs=-1)
@SSCLIGroup.command('build')
@click.pass_context
def build(ctx, ss, build_dir, dev_img):
    r_dict = utils.resources_in_path(ctx.obj['input_dir'], include_filter=Subsystem)
    if len(ss) == 0:
        for s in r_dict.values():
            s.build(build_dir)
    else:
        for s in ss:
            if s in r_dict:
                r_dict[s].build(build_dir)
            else:
                click.echo(f'Subsystem {s} not found.', err=True)
            


@click.option('--build-dir', type=str, required=False, default='build')
@click.argument('SS_ID', type=str)
@SSCLIGroup.command('run')
@click.pass_context
def run_ss(ctx, ss_id, build_dir):
    r_dict = utils.resources_in_path(ctx.obj['input_dir'], include_filter=Subsystem)

    if not ss_id in r_dict:
        click.echo(f'{ss_id} not found in input resources. [{", ".join(r_dict.keys())}]', err=True)
        click.echo(r_dict)
        exit(1)

    ss_cls = r_dict[ss_id]

    ss_build_base = os.path.join(build_dir, ss_cls._RESOURCE_NAME)
    ss_bin_dir = os.path.join(ss_build_base, 'bin')
    
    
    if not os.path.exists(ss_bin_dir):
        click.echo(f'{ss_bin_dir} not found. Have you compiled this subsystem?', err=True)
        exit(1)

    sys.path.insert(0, ss_bin_dir)

    ss = ss_cls()

    loop = asyncio.get_event_loop()
    loop.run_until_complete(ss.run())
    loop.close()
    

@click.option('--empty', type=bool, help="Don't populate example subfields.", is_flag=True)
@click.option('--out-dir', type=click.Path(exists=True), required=False, default='inputs')
@click.option('--description', type=str, required=False)
@click.argument('NAME', type=str)
@SSCLIGroup.command('create', help='Create a new subsytem.')
@click.pass_context
def create(ctx, name, out_dir, description, empty):
    utils.template_to_path(
        SSI_PY_TEMPLATE,
        os.path.join(out_dir, f'{name}.py'),
        **{
            'ss_name': name,
            'ss_description': description or name,
            'to_camel': utils.to_camel,
            'is_empty': empty
        }
    )
