from stitches_py.resources import field, subfield

@field()
class DetectorConfig:
    """
        Configuration for an ObjectDetector
    """
    
    @subfield
    def detector_id(self) -> str:
        """
            Unique identifier of the ObjectDetector
        """
        pass