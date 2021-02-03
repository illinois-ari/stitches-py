from stitches_py.resources import field, subfield

@field()
class RecorderConfig:
    """
        Configuration for an Streamer
    """
    
    @subfield
    def port(self) -> int:
        """
            Port to stream on.
        """
        pass