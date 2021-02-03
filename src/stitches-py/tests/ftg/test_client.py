from stitches_py.resources.ftg import FTGRepoClient


def test_client_init():
    client = FTGRepoClient()

    assert client