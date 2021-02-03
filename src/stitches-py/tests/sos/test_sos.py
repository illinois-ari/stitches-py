import pytest
from stitches_py.resources import system_of_systems, SystemOfSystems, sos_connection, sos_subsystem, Subsystem, subsystem

@pytest.fixture()
def mock_sos():
    @subsystem()
    class MockSS:
        pass


    # This needs to be DRYed
    @system_of_systems()
    class MockSoS():
        @sos_subsystem
        def foo(self) -> MockSS:
            """ Foo SS (MockSS)  """
            pass


    return MockSoS



def test_ss_xml(mock_sos):
    xmlstr = mock_sos.to_stitches_xml()

    print(xmlstr)

    # TODO: Validate xml
