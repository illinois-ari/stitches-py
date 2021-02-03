import asyncio

from collections import OrderedDict
from copy import copy
import docker
from enum import Enum
import functools
import importlib
import ipaddress
import logging
import os
import socket
from lxml import etree
from xml.etree import ElementTree as ET
import subprocess
import typing as t

from stitches_py import consts as c
from stitches_py.resources.base import resource, Field
from stitches_py.resources.ss import Subsystem
from stitches_py.templates import ss as ss_tmps, sos as sos_tmps
from stitches_py import utils

@resource()
class SoSSubsystem:
    """ SoS Connection Resource """
    ss_cls: t.Type[Subsystem]
    devices: t.List[str]
    extra_volumes: t.List[str]
    gpu_enabled: bool


@resource()
class SoSConnection:
    """ SoS Connection Resource """
    src_ss: str
    src_int: str
    src_field: t.Type[Field]
    dest_ss: str
    dest_int: str
    dest_field: t.Type[Field]

    def __init__(self, src_ss: str, src_int: str, dest_ss: str, dest_int: str):
        self.src_ss = src_ss
        self.src_int = src_int
        self.dest_ss = dest_ss
        self.dest_int = dest_int


@resource()
class SystemOfSystems:
    _SUBSYSTEM_MAP: t.Dict[str, t.Type[SoSSubsystem]]
    _CONNECTIONS: t.List[SoSConnection]

    @classmethod
    def build(
            cls,
            build_dir: str,
    ):
        return cls.deploy(build_dir)

    @classmethod
    def deploy(
            cls,
            build_dir: str,
            *,
            image_registry: str = f'{socket.gethostname()}:5000',
            subnet_cidr: str = '10.222.222.0/22',
            ss_node_map = None
        ):
        build_path = os.path.abspath(build_dir)

        if not os.path.exists(build_path):
            os.mkdir(build_path)
        elif not os.path.isdir(build_path):
            raise ValueError('Provided build path is not a directory')

        sos_out_path = os.path.join(build_path, cls._RESOURCE_NAME)

        if not os.path.exists(sos_out_path):
            os.mkdir(sos_out_path)

        cur_ip = ipaddress.ip_address(subnet_cidr.split('/')[0])
        
        ss_ip_map = {}
        for ss_name in cls._SUBSYSTEM_MAP.keys():
            ss_ip_map[ss_name] = cur_ip
            cur_ip += 2 # Skip ips for SS ans SSHCAL

        sos_xml_path = os.path.join(sos_out_path, f'{cls._RESOURCE_NAME}.xml')

        with open(sos_xml_path, 'wb') as f:
            f.write(cls.to_stitches_xml(ss_ip_map))

        specs_dir = os.path.join(c.INPUT_DIR, 'SS-STITCHES_Specs')
        if not os.path.exists(specs_dir):
            os.mkdir(specs_dir)

        for ss_name, ss in cls._SUBSYSTEM_MAP.items():
            ss_cls = ss.ss_cls
            ss_xml_path = os.path.join(specs_dir, f'{ss_name}_SSI.xml')

            with open(ss_xml_path, 'wb') as f:
                f.write(ss_cls.to_stitches_xml(name_override=f'{cls._RESOURCE_NAME}.{ss_name}'))

        cmd = [
            f'{c.CAP_DIR}/SysInteg/scripts/BuildSoS.sh',
            sos_xml_path,
            '-nocompile',
            '-v'
        ]

        env = copy(os.environ)
        env.update({
            'PYTHONPATH': '/usr/local/lib/python2.7/dist-packages',
            'FTG_HOST_PORT': '4567',
            'FTG_HOST_IP': 'localhost'
        })
        proc = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=os.path.abspath(sos_out_path),
        )

        print(f'[{cmd!r} exited with {proc.returncode}]')

        if proc.stdout:
            print(f'[stdout]\n{proc.stdout.decode()}')
        if proc.stderr:
            print(f'[stderr]\n{proc.stderr.decode()}')


        if ss_node_map is None:
            ss_node_map = {}
            for ss_name in cls._SUBSYSTEM_MAP.keys():
                ss_node_map[ss_name] = socket.gethostname()

        sos_build_dir = os.path.join(sos_out_path, f'build_{cls._RESOURCE_NAME}')

        temp_vars = dict(
            sos=cls,
            sos_mod=cls._RESOURCE_MODULE,
            sos_name=cls._RESOURCE_NAME,
            ss_map=cls._SUBSYSTEM_MAP,
            ss_node_map=ss_node_map,
            ss_ip_map=ss_ip_map,
            subnet_cidr=subnet_cidr,
            to_camel=utils.to_camel,
            image_registry=image_registry
        )

        utils.template_to_path(
            sos_tmps.HCAL_CMAKE_TEMPLATE,
            os.path.join(sos_build_dir, 'CMakeLists.txt'),
            **temp_vars
        )

        for ss_name, ss_cls in cls._SUBSYSTEM_MAP.items():
            ss_temp_vars = {
                'ss_name': ss_name,
                'image_registry': image_registry
            }
            sos_ssi_out_path = os.path.join(sos_build_dir, f'gen_ConfiguredSS_{ ss_name }')
            utils.template_to_path(    
                sos_tmps.SOS_SSI_CMAKE_TEMPLATE,
                os.path.join(sos_ssi_out_path, 'CMakeLists.txt'),
                **ss_temp_vars
            )

            utils.template_to_path(    
                sos_tmps.HCAL_DOCKERFILE_TEMPLATE,
                os.path.join(sos_ssi_out_path, 'Dockerfile'),
                **ss_temp_vars
            )
            utils.template_to_path(    
                sos_tmps.HCAL_ENTRYPOINT_TEMPLATE,
                os.path.join(sos_ssi_out_path, 'entrypoint.sh'),
                **ss_temp_vars
            )
            cmd = [
                'sudo',
                '-E',
                'docker',
                'buildx',
                'build',
                '--platform', 'amd64,arm64',
                '--push',
                '-t', f'{image_registry}/{ss_name.lower()}-hcal',
                '.'
            ]

            cmd = [
                'sudo',
                '-E',
                'docker',
                'build',
                '-t', f'{image_registry}/{ss_name.lower()}-hcal',
                '.'
            ]
                
            proc = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=os.path.join(sos_ssi_out_path),
            ) 

            print(f'[{cmd!r} exited with {proc.returncode}]')

            if proc.stdout:
                print(f'[stdout]\n{proc.stdout.decode()}')
            if proc.stderr:
                print(f'[stderr]\n{proc.stderr.decode()}')



        utils.template_to_path(    
            sos_tmps.SOS_COMPOSE_TEMPLATE,
            os.path.join(sos_out_path, 'docker-compose.yaml'),
            **temp_vars
        )

        cmd = [
            'sudo',
            '-E',
            'docker-compose',
            'up',
            '-d'
        ]
            
        proc = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=os.path.join(sos_build_dir),
        )


        print(f'[{cmd!r} exited with {proc.returncode}]')

        if proc.stdout:
            print(f'[stdout]\n{proc.stdout.decode()}')
        if proc.stderr:
            print(f'[stderr]\n{proc.stderr.decode()}')


    @classmethod
    def to_stitches_xml(cls, ss_ip_map: t.Dict[str, str]):
        sos_el = etree.Element('SoS')
        sos_el.attrib['xmlns'] = 'STITCHES'
        sos_el.attrib['{http://www.w3.org/2001/XMLSchema-instance}schemaLocation'] = 'STITCHES //STITCHES_Capabilities/SystemEngineering/SoS_Specification.xsd'
        
        # Version Element
        etree.SubElement(sos_el, 'STITCHESVersion').text = '0.6'


        comps_el = etree.SubElement(sos_el, 'Components')
        conns_el = etree.SubElement(sos_el, 'Connections')

        sss_el = etree.SubElement(comps_el, 'SubSystems')
        # Not sure what OCEs are
        oces_el = etree.SubElement(comps_el, 'OpenComputeEnvironments')

        oce1_el = etree.SubElement(oces_el, 'OpenComputeEnvironment')

        oce1_el.attrib['Name'] = 'OCE1'
        etree.SubElement(oce1_el, 'OCESpecificationFile').text = 'OCE1.xml'

        oce1_ip_el = etree.SubElement(oce1_el, 'IPAddress')
        etree.SubElement(oce1_ip_el, 'IPAddressBegin').text = '10.200.7.100'
        etree.SubElement(oce1_ip_el, 'IPAddressEnd').text = '10.200.7.200'

        oce1_port_el = etree.SubElement(oce1_el, 'Port')
        etree.SubElement(oce1_port_el, 'PortBegin').text = '6000'
        etree.SubElement(oce1_port_el, 'PortEnd').text = '7000'

        # Services -> Components
        for ss_name, ss in cls._SUBSYSTEM_MAP.items():
            ss_cls = ss.ss_cls

            ss_el = etree.SubElement(sss_el, 'SubSystem')

            ss_el.attrib['Name'] = ss_name
            ss_el.attrib['{http://www.w3.org/2001/XMLSchema-instance}type'] = "Atomic"
            
            etree.SubElement(ss_el, 'SS-STITCHESSpecificationFile').text = f'{ss_name}_SSI.xml'

            # What do these do?
            ip_el = etree.SubElement(ss_el, 'IPAddress')
            
            etree.SubElement(ip_el, 'IPAddressBegin').text = str(ss_ip_map[ss_name])
            etree.SubElement(ip_el, 'IPAddressEnd').text = str(ss_ip_map[ss_name])

            port_el = etree.SubElement(ss_el, 'Port')
            
            etree.SubElement(port_el, 'PortBegin').text = '6000'
            etree.SubElement(port_el, 'PortEnd').text = '7000'

        for conn_method in cls._CONNECTIONS:
            conn = SoSConnection(
                conn_method._SRC_SS,
                conn_method._SRC_INT,
                conn_method._DEST_SS,
                conn_method._DEST_INT,
            )
            conn_el = etree.SubElement(conns_el, 'Connection')
            
            src_el = etree.SubElement(conn_el, 'Source')
            etree.SubElement(src_el, 'SSName').text = conn.src_ss
            etree.SubElement(src_el, 'InterfaceName').text = f'{utils.to_camel(conn.src_int)}Out'

            dest_el = etree.SubElement(conn_el, 'Destination')
            etree.SubElement(dest_el, 'SSName').text = conn.dest_ss
            etree.SubElement(dest_el, 'InterfaceName').text = f'{utils.to_camel(conn.dest_int)}In'

            flows_el = etree.SubElement(conn_el, 'MessageFlows')
            flow_el = etree.SubElement(flows_el, 'MessageFlow')

            src_msg_el = etree.SubElement(flow_el, 'SourceMessageName')
            src_msg_el.text = f'{utils.to_camel(conn.src_int)}OutOutMessage'
            src_msg_el.attrib['SSName'] = str(conn.src_ss)
            src_msg_el.attrib['InterfaceName'] = f'{utils.to_camel(conn.src_int)}Out'

            dest_msg_el = etree.SubElement(flow_el, 'DestinationMessageName')
            dest_msg_el.text = f'{utils.to_camel(conn.dest_int)}InInMessage'
            dest_msg_el.attrib['SSName'] = str(conn.dest_ss)
            dest_msg_el.attrib['InterfaceName'] = f'{utils.to_camel(conn.dest_int)}In'

        etree.SubElement(sos_el, 'MessageFrequencyDefault').text = '1.0'
        etree.SubElement(sos_el, 'STITCHESFrameworkFile').text = 'STITCHES_Framework1.xml'

        return ET.tostring(sos_el)


def sos_connection(src_ss: str, src_int: str, dest_ss: str, dest_int: str):
    """
    Decorator for annotating SoS connections
    """
    def _wrapper(i_method: t.Callable):
        setattr(i_method, '_IS_CONNECTION', True)
        setattr(i_method, '_SRC_SS', src_ss)
        setattr(i_method, '_SRC_INT', src_int)
        setattr(i_method, '_DEST_SS', dest_ss)
        setattr(i_method, '_DEST_INT', dest_int)

        return i_method

    return _wrapper


def sos_subsystem(*, extra_volumes: t.List[str] = [], devices: t.List[str] = [], gpu_enabled: bool = False):
    """
    Decorator for annotating SoS connections
    """
    def _inner(i_method: t.Callable) -> t.Type:
        setattr(i_method, '_IS_SUBSYSTEM', True)
        setattr(i_method, '_SS_VOLUMES', extra_volumes)
        setattr(i_method, '_SS_DEVICES', devices)
        setattr(i_method, '_SS_GPU_ENABLED', gpu_enabled)
        return i_method

    return _inner



def system_of_systems():
    """
    Decorator for annotating SoS classes.
    """
    def _inner(sos_cls: t.Type) -> t.Type:
        sos_cls = resource(
            group='sos',
            base_resources=[SystemOfSystems]
        )(sos_cls)

        ss_map = dict()
        connections = list()

        attr_dict = {}

        # Iterate over cls members
        for m_name, m_obj in sos_cls.__dict__.items():
            # Find Subsystems
            if hasattr(m_obj, '_IS_SUBSYSTEM'):
                ret_anno = m_obj.__annotations__.get('return', None)

                if not ret_anno:
                    raise Exception('Subsystem properties must have a return annotation')
                
                attr_dict[f'_{m_obj.__name__}'] = None
                attr_dict[m_obj.__name__] = property(
                    utils.wrap_property(m_obj),
                    utils.wrap_setter(m_obj)
                )
                ss = SoSSubsystem()
                ss.ss_cls = ret_anno
                ss.devices = getattr(m_obj, '_SS_DEVICES', [])
                ss.extra_volumes = getattr(m_obj, '_SS_VOLUMES', [])
                ss.gpu_enabled = getattr(m_obj, '_SS_GPU_ENABLED', False)
                ss_map[m_name] = ss
            elif hasattr(m_obj, '_IS_CONNECTION'):
                connections.append(m_obj)


        attr_dict.update({
            '_SUBSYSTEM_MAP': ss_map,
            '_CONNECTIONS': connections,
        })

        all_types = [sos_cls, SystemOfSystems]

        return type(sos_cls.__name__, tuple(all_types), attr_dict)

    return _inner
