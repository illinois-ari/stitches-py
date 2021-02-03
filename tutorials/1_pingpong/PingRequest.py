from stitches_py.resources import field, subfield

@field()
class PingRequest:
    """
    PingRequest
    """

    @subfield
    def req_id(self) -> str:
        """ UUID used to track requests. """
        pass
    
    @subfield
    def send_ts(self) -> int:
        """Time (in milliseconds) when the request was sent."""
        pass