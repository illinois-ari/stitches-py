from stitches_py.resources import field, subfield

@field()
class CameraConfig:
    """
        Configuration for an Camera
    """
    
    @subfield
    def device_id(self) -> str:
        """
            Camera video device.
        """
        pass

    @subfield
    def frame_width(self) -> int:
        """
            Camera frame width.
        """
        pass

    @subfield
    def frame_height(self) -> int:
        """
            Camera frame height.
        """
        pass