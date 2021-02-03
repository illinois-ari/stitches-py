from stitches_py.resources import field, subfield

@field()
class PongResponse:
    """
    PongResponse
    """
    @subfield
    def req_id(self) -> str:
        """ID of the received request."""
        pass

    @subfield
    def recv_ts(self) -> int:
        """Time (in milliseconds) when the request was received."""
        pass