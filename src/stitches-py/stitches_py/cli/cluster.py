import click
import os
import signal
import json
import docker
from tabulate import tabulate
import sys


@click.group('cluster', help='Cluster commands')
@click.pass_context
def ClusterCLIGroup(ctx):
    pass

@ClusterCLIGroup.command('status', help='Get Cluster Status')
@click.pass_context
def cluster_status(ctx):
    client = docker.from_env()
    client.swarm.reload()
    print(json.dumps(client.swarm.attrs, indent=4))


@ClusterCLIGroup.command('nodes', help='Get Cluster nodes')
@click.pass_context
def list_nodes(ctx):
    client = docker.from_env()
    attrs_list = [n.attrs for n in client.nodes.list()]
    print(json.dumps(attrs_list, indent=4))