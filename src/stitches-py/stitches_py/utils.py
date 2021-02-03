import glob
import importlib.util
import jinja2
import os
import typing as t

def is_resource(obj) -> bool:
    return hasattr(obj, '_RESOURCE_ID')


def resources_in_path(
    path: str,
    *,
    include_external=False,
    recurse=True,
    include_filter: t.Type = None
) -> t.Dict[str, t.Type]:

    r_dict = dict()
    if not recurse:
        glob_str = os.path.join(path, '*.py')
        
    else:
        glob_str = os.path.join(path, '**', '*.py')

    py_files = glob.glob(glob_str, recursive=recurse)

    for pyf in py_files:
        r_dict.update(
            resources_in_file(
                pyf,
                include_external=include_external,
                include_filter=include_filter
            )
        )

    return r_dict
    

def resources_in_file(
    file_path: str,
    *,
    include_external=False,
    include_filter: t.Type = None
) -> t.Dict[str, t.Type]:
    resources = dict()
    try:
        mod = load_mod_from_file(file_path)

        resources = resources_in_module(
            mod,
            include_external=include_external,
            include_filter=include_filter
        )
    except Exception as e:
        print(e)

    return resources


def resources_in_module(
    mod,
    *,
    include_external=False,
    include_filter: t.List[t.Type] = None
) -> t.Dict[str, t.Type]:
    r_dict = dict()
    mod_name = mod.__name__
    if '_' in mod_name:
        mod_name = to_camel(mod_name)

    mod_name = mod_name.lower() # TODO: Messy workaround to some c compile issues
    
    
    for m_obj in mod.__dict__.values():
        if is_resource(m_obj):
            include_resource = True

            if not (m_obj._RESOURCE_MODULE == mod_name or include_external):
                include_resource = False

            if (include_filter != None) and (include_filter not in m_obj._BASE_RESOURCES):
                include_resource = False
            
            if include_resource:
                r_dict[m_obj._RESOURCE_ID] = m_obj

    return r_dict


def load_mod_from_file(file_path: str, *, mod_prefix: str = None):
    mod_name = os.path.splitext(os.path.basename(file_path))[0]
    
    if mod_prefix:
        mod_name = f'{mod_prefix}.{mod_name}'

    mod_spec = importlib.util.spec_from_file_location(mod_name, file_path)
    mod = importlib.util.module_from_spec(mod_spec)
    mod_spec.loader.exec_module(mod)

    return mod


def to_camel(string: str) -> str:
    """
    Convert a string to camel case.
    """
    ss = string.split('_')
    return ''.join([word.capitalize() for word in ss])



def to_lower_camel(string: str) -> str:
    """
    Convert a string to camel case.
    """
    ss = string.split('_')
    return ''.join([ss[0]] + [word.capitalize() for word in ss[1:]])


def template_to_path(template: jinja2.Template, path: str, **kwargs):
    with open(path, 'w') as f:
        f.write(template.render(**kwargs))


def wrap_property(prop):
    def _wrapped_property(self):
        return getattr(self, f'_{prop.__name__}')

    return _wrapped_property

def wrap_setter(prop):
    def _wrapped_setter(self, val):
        setattr(self, f'_{prop.__name__}', val)

    return _wrapped_setter
