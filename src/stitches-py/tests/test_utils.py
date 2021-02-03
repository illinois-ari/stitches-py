import os
import pytest

from stitches_py.resources import Subsystem
import stitches_py.utils as utils


@pytest.fixture()
def root_dir():
    return os.path.dirname(os.path.realpath(__file__))


def test_load_mod(root_dir):
    mod = utils.load_mod_from_file(os.path.join(root_dir, 'data/modules/foo.py'))

    assert mod

def test_load_file_resources(root_dir):
    r_dict = utils.resources_in_file(os.path.join(root_dir, 'data/modules/foo.py'))

    assert r_dict is not None
    assert len(list(r_dict.keys())) == 1


def test_load_path_resources(root_dir):
    r_dict = utils.resources_in_path(os.path.join(root_dir, 'data/modules'))

    assert r_dict is not None
    assert len(list(r_dict.keys())) == 3

    filted_dict = utils.resources_in_path(os.path.join(root_dir, 'data/modules'), include_filter=Subsystem)

    print(Subsystem._BASE_RESOURCES)
    assert len(list(filted_dict.keys())) == 1



