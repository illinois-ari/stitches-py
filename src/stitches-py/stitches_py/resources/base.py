import importlib
import logging
import inspect
import os
import typing_inspect as ti
import pkg_resources
import sys
import typing as t

from collections import OrderedDict
from enum import Enum

from pydantic import BaseModel, Field, Extra
from pydantic.fields import ModelField, FieldInfo

from stitches_py.utils import to_camel

class _BaseModel(BaseModel):
    class Config:
        json_encoders = {
                type: lambda v: f'{v.__module__}.{v.__name__}'
            }

class BaseType(_BaseModel):
    pass

class AnyType(BaseType):
    pass

class ScalarType(BaseType):
    type: t.Type


class MethodType(BaseType):
    pass


class ResourceType(BaseType):
    type: t.Type


class ListType(BaseType):
    type: BaseType


class MapType(BaseType):
    key_type: BaseType
    value_type: BaseType


class UnionType(BaseType):
    allowed_types: t.List[BaseType]


class ResourceRef(_BaseModel):
    uid: str
    name: str
    path: str


class ResourceMember(_BaseModel):
    name: str


class ResourceProperty(ResourceMember):
    type: BaseType

    @classmethod
    def from_pydantic(cls, field: ModelField):
        return cls(name=field.name)


def type_from_annotation(annotation):
    if annotation == inspect._empty:
        return None
    elif annotation == t.Any:
        return AnyType()
    elif ti.is_generic_type(annotation):
        g_origin = ti.get_origin(annotation)
        g_args = ti.get_args(annotation)

        if g_origin in [list]: # Better way?
            base_type = type_from_annotation(g_args[0])
            
            return ListType(type=base_type)
        
        elif g_origin in [dict]:  # Better way?
            key_type = type_from_annotation(g_args[0])
            value_type = type_from_annotation(g_args[1])
            
            return MapType(
                key_type=key_type,
                value_type=value_type
            )
    elif inspect.isclass(annotation):
        if issubclass(annotation, BaseResource):
            return ResourceType(type=annotation)
        else:
            return ScalarType(type=annotation)
    else:
        raise Exception(f'Unhandled annotation {annotation}')


class ResourceParameterSpec(_BaseModel):
    name: str
    type: t.Optional[BaseType]

    @classmethod
    def from_sig_param(cls, param: inspect.Parameter):
        return cls(
            name=param.name,
            type=type_from_annotation(param.annotation)
        )

class ResourcePropertySpec(_BaseModel):
    name: str
    return_type: BaseType = None

    @classmethod
    def from_method(cls, m: t.Callable):
        m_sig = inspect.signature(m)
        m_spec = cls(
            name=m.__name__
        )

        m_spec.return_type = type_from_annotation(m_sig.return_annotation)

        return m_spec


class ResourceEventSpec(_BaseModel):
    name: str
    return_type: BaseType = None

    @classmethod
    def from_method(cls, m: t.Callable):
        m_sig = inspect.signature(m)
        m_spec = cls(
            name=m.__name__
        )

        m_spec.return_type = type_from_annotation(m_sig.return_annotation)

        return m_spec


class ResourceMethodSpec(_BaseModel):
    name: str
    input_parameters: t.Dict = Field(default_factory=OrderedDict)
    return_type: BaseType = None

    @classmethod
    def from_method(cls, m: t.Callable):
        m_sig = inspect.signature(m)
        m_spec = cls(
            name=m.__name__
        )

        for name, param in m_sig.parameters.items():
            # Don't include first param for bound methods.
            if name not in ['self', 'cls']:
                m_spec.input_parameters[name] = ResourceParameterSpec.from_sig_param(param)

        m_spec.return_type = type_from_annotation(m_sig.return_annotation)

        return m_spec




class BaseResource:
    _RESOURCE_ID: str
    _RESOURCE_GROUP: str
    _RESOURCE_MODULE: str
    _RESOURCE_NAME: str
    _RESOURCE_DESCRIPTION: str
    _RESOURCE_PATH: str


    _BASE_RESOURCES: t.List[t.Type] = list()

    _RESOURCE_METHODS: t.List[t.Callable]
    _RESOURCE_EVENTS: t.List[t.Callable]
    _RESOURCE_THREADS: t.List[t.Callable]

    _logger: logging.Logger

    def __init__(self):
        self._logger = logging.getLogger(self._RESOURCE_ID)
        self._logger.setLevel(logging.INFO)

    @classmethod
    def is_subtype(cls, other_type: t.Type):
        return other_type in cls._BASE_RESOURCES



def resource(
        *,
        base_resources: t.List[t.Type[BaseResource]] = list(),
        group: str = 'core'
    ):

    def _inner(r_cls: t.Type) -> t.Type:
        r_mod = r_cls.__module__.split('.')[0]

        if '_' in r_mod:
            r_mod = to_camel(r_mod)

        r_mod = r_mod.lower()

        attr_dict = dict(r_cls.__dict__)
        attr_dict.update({
            '__name__': r_cls.__name__,
            '__module__': r_cls.__module__,
            '__doc__': r_cls.__doc__,
            '_RESOURCE_ID': f'{r_mod}.{group}.{r_cls.__name__}',
            '_RESOURCE_GROUP': group,
            '_RESOURCE_NAME': r_cls.__name__,
            '_RESOURCE_DESCRIPTION': r_cls.__doc__,
            '_RESOURCE_MODULE': r_mod,
            '_RESOURCE_PATH': f'{r_cls.__module__}',
            '_BASE_RESOURCES': base_resources
        })

        all_types = [r_cls, BaseResource]

        return type(resource.__name__, tuple(all_types), attr_dict)

    return _inner



def get_module_resources(mod_path: str) -> t.Dict[str, t.Type]:
    mod = importlib.import_module(mod_path)
    resources = dict()
    for o in dir(mod):
        o_obj = getattr(mod, o)
        o_type = type(o_obj)

        if not inspect.isclass(o_obj) and hasattr(o_obj, '_CBALL_TYPE_ID') and hasattr(o_obj, '_CBALL_RESOURCE_ID'):
            r_type_id = getattr(o_obj, '_CBALL_TYPE_ID')

            if r_type_id not in resources:
                resources[r_type_id] = set()


            resources[r_type_id].add(o_obj)

    return resources

def get_module_resource_types(mod_path: str) -> t.Dict[str, t.Type]:
    mod = importlib.import_module(mod_path)
    resource_types = dict()
    for o in dir(mod):
        o_obj = getattr(mod, o)

        if inspect.isclass(o_obj) and hasattr(o_obj, '_CBALL_TYPE_ID'):
            type_id = getattr(o_obj, '_CBALL_TYPE_ID')

            resource_types[type_id] = o_obj

    return resource_types

def is_resource(obj: t.Any) -> bool:
    return hasattr(obj, 'CBALL_IS_RESOURCE')


def get_resource_id(obj: t.Any) -> str:
    return getattr(obj, '_CBALL_RESOURCE_ID')