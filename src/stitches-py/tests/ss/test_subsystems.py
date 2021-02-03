import pytest
from stitches_py.resources import subsystem, Subsystem, ss_interface, ss_thread
from stitches_py.resources.ftg import Field, field, subfield, FTGField

@pytest.fixture()
def mock_ss():
    # This needs to be DRYed
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



    @subsystem()
    class MockSS():
        
        @ss_interface
        def wo(self, in_var: MockField):
            pass

        @ss_interface
        def ro(self) -> MockField:
            pass

        @ss_interface
        def rw(self, in_var: MockField) -> MockField:
            pass

        @ss_thread
        def _thead_1(self):
            pass
        

    return MockSS



def test_ss_markup(mock_ss):
    assert mock_ss._IN_INTERFACES
    assert len(mock_ss._IN_INTERFACES) == 2

    assert mock_ss._OUT_INTERFACES
    assert len(mock_ss._OUT_INTERFACES) == 2

    assert mock_ss._SS_THREADS
    assert len(mock_ss._SS_THREADS) == 1

    ss_obj = mock_ss()
    assert ss_obj._IN_INTERFACES
    assert len(ss_obj._IN_INTERFACES) == 2

    assert ss_obj._OUT_INTERFACES
    assert len(ss_obj._OUT_INTERFACES) == 2

    assert ss_obj._SS_THREADS
    assert len(ss_obj._SS_THREADS) == 1  



def test_ss_xml(mock_ss):
    xmlstr = mock_ss.to_stitches_xml()

    print(xmlstr)

    # TODO: Validate xml


def test_ss_xml(mock_ss):
    xmlstr = mock_ss.to_stitches_xml()

    print(xmlstr)

    # TODO: Validate xml