import pytest
from stitches_py.resources.ftg import Field, field, subfield, FTGField

@pytest.fixture()
def mock_field():

    @field()
    class MockField():
        @subfield
        def foo(self) -> str:
            """ Foo subfield  """
            pass
        
        @subfield
        def bar(self) -> int:
            """ Bar subfield  """
            pass


    return MockField


def test_field_markup(mock_field):
    assert isinstance(mock_field._SUB_FIELDS, list)
    assert len(mock_field._SUB_FIELDS) == 2


def test_field_init(mock_field):
    f = mock_field()

    assert f.foo == None
    assert f.bar == None


def test_field_set(mock_field):
    f = mock_field()
    f.foo = "test"

    assert f.foo == "test"


def test_to_ftg(mock_field):
    m_ftg = FTGField.from_resource(mock_field)

    assert m_ftg
    assert len(m_ftg.subfields.subfield) == 2
