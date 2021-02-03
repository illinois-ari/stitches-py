import click
import os
import signal
import json
from tabulate import tabulate
import sys

from stitches_py.resources import SystemOfSystems
from stitches_py import utils

@click.group('sos', help='SoS commands')
@click.pass_context
def SoSCLIGroup(ctx):
    pass

@SoSCLIGroup.command('list', help='List SoS')
@click.pass_context
def list_sos(ctx):
    r_dict = utils.resources_in_path(ctx.obj['input_dir'], include_filter=SystemOfSystems)
    headers = ["ID", "Description"]
    click.echo(tabulate([(k,) + (v._RESOURCE_DESCRIPTION,) for k,v in r_dict.items()], headers=headers))


@click.option('--build-dir', type=click.Path(exists=True), required=False, default='build')
@click.argument('sos', type=str)
@SoSCLIGroup.command('build')
@click.pass_context
def build(ctx,  sos, build_dir):
    r_dict = utils.resources_in_path(ctx.obj['input_dir'], include_filter=SystemOfSystems)
    
    if sos not in r_dict.keys():
        click.echo(f'SoS {sos} not found in input directory {ctx.obj["input_dir"]}')
        exit(1)
    
    click.echo(f'Deploying {sos}')
    
    sos_cls = r_dict[sos]
    sos_cls.build(build_dir)
