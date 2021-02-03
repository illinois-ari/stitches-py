from collections import OrderedDict
from copy import copy
from enum import Enum
import functools
import importlib
import inspect
import logging
import os
import shutil
import sys
import time
import threading
import socket
import subprocess
from lxml import etree
from xml.etree import ElementTree as ET
import typing as t

from stitches_py.resources.base import resource, Field
from stitches_py.utils import to_camel

from stitches_py import consts as c, utils

from stitches_py.templates import ss as templates

class InterfaceDirection(Enum):
    IN = 'In'
    OUT = 'Out'


class SSThread:
    name: str
    method: t.Callable

    @classmethod
    def from_method(cls, method):
        t = cls()
        t.method = method
        t.name = method.__name__

        return t

class SSInterface:
    name: str
    type: t.Type
    method: t.Callable
    direction: InterfaceDirection

    @classmethod
    def from_method(cls, meth: t.Callable, direction: InterfaceDirection):
        interface = None
        annotations = copy(meth.__annotations__)

        if direction == InterfaceDirection.OUT:
            if 'return' in annotations:
                interface = cls()
                interface.name = f'{utils.to_camel(meth.__name__)}Out'
                interface.direction = direction
                interface.method = meth
                interface.type = annotations.pop('return')
                
        elif direction == InterfaceDirection.IN:
            # TODO: Dynamic Fields for multi param interfaces.
            annotations.pop('return', None)
            in_vars = list(annotations.keys())

            if len(in_vars) == 1:
                interface = cls()
                interface.name = f'{utils.to_camel(meth.__name__)}In'
                interface.direction = direction
                interface.method = meth
                interface.type = annotations[in_vars[0]]

        return interface

    def __call__(self, *args, **kwargs):
        return self.method(*args, **kwargs)
        



@resource()
class Subsystem:
    _IN_INTERFACES: t.List[SSInterface]
    _OUT_INTERFACES: t.List[SSInterface]
    _INTERFACE_FIELDS: t.List[Field]
    _SS_THREADS: t.List[SSThread]

    _WRAPPER_IMAGE: str

    _threads = list()

    def __init__(self):
        super().__init__()
        self._logger = logging.getLogger(self.__class__.__name__)
        self._shutdown_requested = False
        #self._ssi_upper = None
        self._threads = list()
        self._int_cb = None

        self.init()

    @classmethod
    def build(
        cls,
        build_dir: str,
        *,
        cross_platform: bool = False,
        image_registry: str = f'{socket.gethostname()}:5000'
    ):
        build_path = os.path.abspath(build_dir)
        if not os.path.isdir(build_path):
            raise ValueError('Provided build path is not a directory')

        if not os.path.exists(build_path):
            os.mkdir(build_path)
           
        ss_out_path = os.path.join(build_path, cls._RESOURCE_NAME)

        if os.path.exists(ss_out_path):
            shutil.rmtree(ss_out_path, ignore_errors=True)
        
        os.mkdir(ss_out_path)
       
        if not os.path.exists(ss_out_path):
            os.mkdir(ss_out_path)

        ssi_xml_path = os.path.join(ss_out_path, f'{cls._RESOURCE_NAME}_SSI.xml')

        with open(ssi_xml_path, 'wb') as f:
            f.write(cls.to_stitches_xml())

        #cmd = ['/bin/bash', '-c', f'"{c.CAP_DIR}/SysInteg/scripts/BuildSSI.sh {ssi_xml_path} C++11"']
        cmd = [f'{c.CAP_DIR}/SysInteg/scripts/BuildSSI.sh', ssi_xml_path, 'C++11']

        proc = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=os.path.abspath(ss_out_path),
        )
        print(f'[{cmd!r} exited with {proc.returncode}]')


        if proc.stdout:
            print(f'[stdout]\n{proc.stdout.decode()}')
        if proc.stderr:
            print(f'[stderr]\n{proc.stderr.decode()}')


        def field_to_c(field: Field) -> str:
            return f'{field._RESOURCE_MODULE }::{ field._RESOURCE_GROUP }::{ field._RESOURCE_NAME }'

        def type_to_c(c_type: t.Type) -> str:
            if c_type == str:
                return 'std::string'
            elif c_type == int:
                return 'int32_t'
            elif c_type == float:
                return 'double'
            elif c_type == bool:
                return 'bool'
            return ''

        ss_fields = list()

        for interface in cls._IN_INTERFACES + cls._OUT_INTERFACES:
            if interface.type not in ss_fields:
                ss_fields.append(interface.type)

        # Declare template variables
        temp_vars = dict(
            ss=cls,
            ss_mod=cls._RESOURCE_MODULE,
            ss_name=cls._RESOURCE_NAME,
            in_ints=cls._IN_INTERFACES,
            out_ints=cls._OUT_INTERFACES,
            wrapper_image=cls._WRAPPER_IMAGE,
            field_to_c=field_to_c,
            to_camel=utils.to_camel,
            type_to_c=type_to_c,
            ss_fields=ss_fields,
            image_registry=image_registry
        )

        # Template custom source files
        ssi_src_dir = os.path.join(ss_out_path, 'Stitches/src')


        # SSIUpper class
        utils.template_to_path(
            templates.SSI_UPPER_TEMPLATE,
            os.path.join(ssi_src_dir, f'{cls._RESOURCE_NAME}SSIUpper.cpp'),
            **temp_vars
        )

        # SSI Pybind class
        utils.template_to_path(
            templates.SSI_PYBIND_TEMPLATE,
            os.path.join(ssi_src_dir, f'{cls._RESOURCE_NAME}PyBind.cpp'),
            **temp_vars
        )
        
        # SSI main class
        utils.template_to_path(
            templates.SSI_MAIN_TEMPLATE,
            os.path.join(ssi_src_dir, f'{cls._RESOURCE_NAME}Main.cpp'),
            **temp_vars
        )

        # SSI CMake
        utils.template_to_path(
            templates.SSI_CMAKE_TEMPLATE,
            os.path.join(ss_out_path, 'CMakeLists.txt'),
            **temp_vars
        )

        # SSI build.sh
        utils.template_to_path(
            templates.SSI_BUILD_SH_TEMPLATE,
            os.path.join(ss_out_path, 'build.sh'),
            **temp_vars
        )
            
        cls_path = os.path.abspath(sys.modules[cls.__module__].__file__)
        shutil.copytree(sys.path[0], os.path.join(ss_out_path, 'inputs'))
        # SSI Docker Image
        utils.template_to_path(
            templates.SSI_DOCKERFILE_TEMPLATE,
            os.path.join(ss_out_path, f'Dockerfile'),
            **temp_vars
        )
        utils.template_to_path(
            templates.SSI_ENTRYPOINT_TEMPLATE,
            os.path.join(ss_out_path, f'entrypoint.sh'),
            **temp_vars
        )



        if cross_platform:
            cmd = [
                'sudo',
                '-E',
                'docker',
                'buildx',
                'build',
                '--platform', 'amd64,arm64',
                '--build-arg', f'IMAGE_REGISTRY={image_registry}',
                '--push',
                '-t', f'{image_registry}/{cls._RESOURCE_NAME.lower()}',
                '.'
            ]
        else:
            cmd = [
                'sudo',
                '-E',
                'docker',
                'build',
                '-t', f'{image_registry}/{cls._RESOURCE_NAME.lower()}',
                '.'
            ]

        proc = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=os.path.join(ss_out_path),
        )


        print(f'[{cmd!r} exited with {proc.returncode}]')

        if proc.stdout:
            print(f'[stdout]\n{proc.stdout.decode()}')
        if proc.stderr:
            print(f'[stderr]\n{proc.stderr.decode()}')

        if cross_platform:
            cmd = [
                'sudo',
                '-E',
                'docker',
                'pull',
                f'{image_registry}/{cls._RESOURCE_NAME.lower()}'
            ]
            
            proc = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=os.path.join(ss_out_path),
            )     


    def init(self):
        try:
            ipc_dir = os.path.join(os.getcwd(), 'ipc')
            pipe_dir = os.path.join(os.getcwd(), 'namedpipes')

            if not os.path.exists(ipc_dir):
                os.mkdir(ipc_dir)

            if not os.path.exists(pipe_dir):
                os.mkdir(pipe_dir)

            for in_int in self._IN_INTERFACES + self._OUT_INTERFACES:
                ipc_path = os.path.join(ipc_dir, in_int.name)
                with open(ipc_path, 'w') as f:
                    f.write(f'./namedpipes/{in_int.name}')


            for in_int in self._IN_INTERFACES:
                pipe_path = os.path.join(pipe_dir, in_int.name)
                if not os.path.exists(pipe_path):
                    os.mkfifo(pipe_path)

            for o_int in self._OUT_INTERFACES:
                setattr(self, o_int.method.__name__, self._wrap_interface(o_int))

        except Exception as e:
            print(e)

    def run(self):
        try:
            self._gather_threads()
            print(f'Found threads {self._threads}')

            for t in self._threads:
                t.start()

            while not self._shutdown_requested:
                time.sleep(5)

        except Exception as e:
            print(e)


    def _wrap_interface(self, interface):
        print(f'Wrapping interface {interface.name}')

        @functools.wraps(interface)
        def _wrapper(*args, **kwargs):
            print(f'Running wrapped interface {interface.name}')
            ret = interface.method(self, *args, **kwargs)

            if self._int_cb and ret is not None:
                self._int_cb(interface.name, ret)

            return ret
        return _wrapper

    def _gather_threads(self):
        """
        Gather coroutines.
        """
        self._threads = list()
        for thread in self._SS_THREADS:
            self._threads.append(threading.Thread(target=thread.method, args=(self,)))


    def _import_ssi_upper_mod(self):
        self._ssi_mod = importlib.import_module(f'{self._RESOURCE_NAME}Ext')

        return self._ssi_mod




    def shutdown(self):
        """
        Trigger subsystem shutdown
        """
        self._logger.warning('Shutdown requested')
        self._shutdown_requested = True
       

    @classmethod
    def to_stitches_xml(cls, *, name_override: str = None) -> str:
        """
        Convert Subsystem class into STITCHES XML representation.
        """
        ss_el = etree.Element('SubSystem')
        ss_el.attrib['xmlns'] = 'STITCHES'
        ss_el.attrib['{http://www.w3.org/2001/XMLSchema-instance}schemaLocation'] = 'STITCHES //STITCHES_Capabilities/SystemEngineering/SS-STITCHES_Specification.xsd'
        
        # Version Element
        etree.SubElement(ss_el, 'STITCHESVersion').text = '0.6'
        etree.SubElement(ss_el, 'SS_TypeName').text = name_override or f'{cls._RESOURCE_MODULE}.{cls._RESOURCE_NAME}'

        
        
        in_ints = OrderedDict()
        out_ints = OrderedDict()

        if len(cls._IN_INTERFACES) > 0:
            in_ints_el = etree.SubElement(ss_el, 'InputInterfaces')
            idx = 0
            for in_int in cls._IN_INTERFACES:
                #TODO: Validation of i_type
                in_int_el = etree.SubElement(in_ints_el, 'Interface')
                in_int_el.attrib['Name'] = in_int.name
                in_msg_el = etree.SubElement(in_int_el, 'Message')
                in_msg_el.attrib['Name'] = f'{in_int.name}InMessage'
                in_msg_el.attrib['FieldType'] = in_int.type._RESOURCE_ID
                in_msg_el.attrib['ID'] = f'{idx}'

                idx += 1

        if len(cls._OUT_INTERFACES) > 0:
            out_ints_el = etree.SubElement(ss_el, 'OutputInterfaces')
            idx = 0
            for out_int in cls._OUT_INTERFACES:
                #TODO: Validation of i_type
                out_int_el = etree.SubElement(out_ints_el, 'Interface')
                out_int_el.attrib['Name'] = out_int.name
                out_msg_el = etree.SubElement(out_int_el, 'Message')
                out_msg_el.attrib['Name'] = f'{out_int.name}OutMessage'
                out_msg_el.attrib['FieldType'] = out_int.type._RESOURCE_ID
                out_msg_el.attrib['ID'] = f'{idx}'

                idx += 1

        # Hardcode adapter config for now
        ssi_el = etree.SubElement(ss_el, 'SSI')


        etree.SubElement(ssi_el, 'Serialization').attrib['Serialization'] = 'GPB'
        etree.SubElement(ssi_el, 'Transport').attrib['Transport'] = 'NamedPipes'

        home_el = etree.SubElement(ssi_el, 'Home')
        etree.SubElement(home_el, 'InterfaceDirectory').text = ''
        etree.SubElement(home_el, 'Startup').text = 'bin/run.sh'

        compute_env_el = etree.SubElement(ss_el, 'ComputeEnvironmentConstraints')
        support_langs_el = etree.SubElement(compute_env_el, 'SupportedProcessLanguages')
        etree.SubElement(support_langs_el, 'Language').attrib['Language'] = 'C++11'

        support_trans_el = etree.SubElement(compute_env_el, 'SupportedTransports')
        zmq_el = etree.SubElement(support_trans_el, 'Transport')
        zmq_el.attrib['Transport'] = 'ZMQ'
        etree.SubElement(zmq_el, 'Language').text = 'C++11'

        support_serial_el = etree.SubElement(compute_env_el, 'SupportedSerializations')
        gpb_el = etree.SubElement(support_serial_el, 'Serialization')
        gpb_el.attrib['Serialization'] = 'GPB'
        etree.SubElement(gpb_el, 'Language').text = 'C++11'

        return ET.tostring(ss_el)


def ss_thread(i_method: t.Callable):
    """
    Decorator for annotating Subsystem Threads
    """
    setattr(i_method, '_IS_THREAD', True)

    return i_method


def ss_interface(i_method: t.Callable):
    """
    Decorator for annotating Subsystem Interfaces
    """
    setattr(i_method, '_IS_INTERFACE', True)

    return i_method


def subsystem(
    *,
    gpu_enabled: bool = False,
    gpu_required: bool = False,
    wrapper_image: str = 'stitches-wrapper',
    wrapper_registry: str = None
):
    """
    Decorator for annotating Subsystem classes.
    """
    def _inner(ss_cls: t.Type) -> t.Type:
        ss_cls = resource(
            group='ss',
            base_resources=[Subsystem]
        )(ss_cls)

        in_ints = list()
        out_ints = list()
        int_fields = list()
        ss_threads = list()
        foo = list()

        # Iterate over cls members
        for m_name, m_obj in ss_cls.__dict__.items():
            # Find interfaces
            if hasattr(m_obj, '_IS_INTERFACE'):
                ssi_in = SSInterface.from_method(m_obj, InterfaceDirection.IN)
                if ssi_in:
                    if ssi_in.type not in int_fields:
                        int_fields.append(ssi_in.type)
                    in_ints.append(ssi_in)

                ssi_out = SSInterface.from_method(m_obj, InterfaceDirection.OUT)
                if ssi_out:
                    if ssi_out.type not in int_fields:
                        int_fields.append(ssi_out.type)
                    out_ints.append(ssi_out)


            elif hasattr(m_obj, '_IS_THREAD'):
                sst = SSThread.from_method(m_obj)
                ss_threads.append(sst)
                foo.append(m_obj.__name__)


        attr_dict = {
            '_IN_INTERFACES': in_ints,
            '_OUT_INTERFACES': out_ints,
            '_INTERFACE_FIELDS': int_fields,
            '_SS_THREADS': copy(ss_threads),

            '_GPU_ENABLED': gpu_enabled,
            '_GPU_REQUIRED': gpu_required,
            '_WRAPPER_IMAGE': wrapper_image
        }

        all_types = [ss_cls, Subsystem]
        

        ss_cls =  type(ss_cls.__name__, tuple(all_types), attr_dict)

        return ss_cls

    return _inner
