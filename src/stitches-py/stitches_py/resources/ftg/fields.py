import logging
import typing as t

from enum import Enum
import typing as t

from stitches_py import utils
from stitches_py.resources.base import resource, BaseType, AnyType, ScalarType, ResourceType, ListType, type_from_annotation


class SubField():
    name: str
    field_type: BaseType

    def __init__(self, name: str, field_type: BaseType):
        self.name = name
        self.field_type = field_type



@resource()
class Field():
    _SUB_FIELDS: t.List[SubField]



def subfield(sf_method: t.Callable):
    """
        Wrapper for subfield properties.
    """
    setattr(sf_method, '_IS_SUB_FIELD', True)
    return sf_method

def field():
    def _inner(field_cls: t.Type) -> t.Type:
        field_cls = resource(
            group='ftg',
            base_resources=[Field]
        )(field_cls)

        attr_dict = {
            '_SUB_FIELDS': list(),
        }

        # Iterate over cls members
        for m_name, m_obj in field_cls.__dict__.items():
            # Find subfields
            if hasattr(m_obj, '_IS_SUB_FIELD'):
                # Convert SubField to property getter/setter
                ret_anno = m_obj.__annotations__.get('return', None)

                if not ret_anno:
                    raise Exception('Subfield properties must have a return annotation')
                
                attr_dict[f'_{m_obj.__name__}'] = None
                attr_dict[m_obj.__name__] = property(
                    utils.wrap_property(m_obj),
                    utils.wrap_setter(m_obj)
                )

                attr_dict['_SUB_FIELDS'].append(SubField(
                    name=m_name,
                    field_type=type_from_annotation(ret_anno)
                ))
      
        all_types = [field_cls, Field]

        return type(field_cls.__name__, tuple(all_types), attr_dict)

    return _inner
