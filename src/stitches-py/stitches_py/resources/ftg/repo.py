from enum import Enum
import typing as t

from pydantic import Field as pyField, BaseModel

from stitches_py.resources.base import BaseType, ScalarType, ResourceType, ListType
from .fields import Field
from stitches_py.utils import to_camel, to_lower_camel


class BaseRepoModel(BaseModel):
    class Config:
        alias_generator = to_lower_camel


def field_type_str(f_type: BaseType) -> str:
    if isinstance(f_type, ScalarType):
        #TODO: More elegant way of doing this.
        if f_type.type == str:
            return 'string'
        elif f_type.type == int:
            return 'integer'
        elif f_type.type == float:
            return 'double'
        elif f_type.type == bool:
            return 'boolean'
    elif isinstance(f_type, ResourceType):
        return f_type._CBALL_TYPE_ID
    elif isinstance(f_type, ListType):
        return f'{field_type_str(f_type.type)}[]'
    else:
        raise ValueError(f'Unupported type {f_type}')


class FTGFieldType(Enum):
    STRING = 'string'
    INTEGER = 'integer'
    DOUBLE = 'double'
    BOOLEAN = 'boolean'


class FTGSubfield(BaseRepoModel):
    name: str
    type: t.Union[str, FTGFieldType]


class FTGSubfields(BaseRepoModel):
    subfield: t.List[FTGSubfield] = pyField(default_factory=list)


def default_mssb():
    return {
        'serialization': [
            {
                'name': 'STITCHESNative',
                'value': -1
            },
            {
                'name': 'GBP',
                'value': -1
            }
        ]
    }

class FTGFieldAnnotation(BaseRepoModel):
    max_serialized_size_bytes: t.Any = pyField(default_factory=default_mssb)
    nested_types: dict = pyField(default_factory=dict)


class FTGField(BaseRepoModel):
    field_type: str
    subfields: FTGSubfields = pyField(default_factory=FTGSubfields)
    field_annotation: FTGFieldAnnotation = pyField(default_factory=FTGFieldAnnotation)

    @classmethod
    def from_resource(cls, resource: t.Type[Field]) -> 'FTGField':
        safe_mod = resource.__module__.split('.')[0].replace('_', '').lower()

        ftg_field =  cls(fieldType = resource._RESOURCE_ID)

        for p in resource._SUB_FIELDS:
            ftg_field.subfields.subfield.append(
                FTGSubfield(
                    name=to_camel(p.name),
                    type=field_type_str(p.field_type)
                )
            )

        return ftg_field


class FTGFieldAddition(BaseRepoModel):
    field_type: FTGField


class FTGPatch(BaseRepoModel):
    """
    FTG Patch
    """
    stitches_version: str = '0.6'
    field_additions: t.List[FTGFieldAddition] = pyField(default_factory=list)


class FTGPatchRequest(BaseRepoModel):
    """
    FTG Patch Request
    """
    patch: FTGPatch