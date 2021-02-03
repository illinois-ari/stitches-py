import base64
import time
from stitches_py.resources import field, subfield

@field()
class CameraFrame:
    """
        Frame from a camera
    """

    def __init__(self):
        import numpy


    def __repr__(self):
        return f'<ts={self.frame_ts} height={self.frame_height} width={self.frame_width} data={self.frame_data[:10]}>'
    
    @subfield
    def frame_idx(self) -> int:
        """
            Index of frame within a series
        """
        pass


    @subfield
    def frame_ts(self) -> float:
        """
            Frame timestamp
        """
        pass


    @subfield
    def frame_height(self) -> int:
        """
            Frame height in pixels
        """
        pass


    @subfield
    def frame_width(self) -> int:
        """
            Frame width in pixels
        """
        pass


    @subfield
    def frame_data(self) -> str:
        """
            Frame data in a byte array
        """
        pass

    @classmethod
    def from_numpy(cls, np_array: 'numpy.ndarray') -> 'CameraFrame':
        import cv2
        cf = cls()
        cf.frame_idx = 0
        cf.frame_ts = time.time()
        cf.frame_height, cf.frame_width, _ = np_array.shape
        
        retval, buffer = cv2.imencode('.jpg', np_array)
        
        cf.frame_data = base64.b64encode(buffer)

        return cf

    @classmethod
    def from_pil(cls, p_img: 'PIL.Image') -> 'CameraFrame':
        import numpy as np
        return cls.from_numpy(np.array(p_img))

    def to_numpy(self) -> 'numpy.ndarray':
        import numpy as np
        import cv2

        np_array = np.frombuffer(base64.b64decode(self.frame_data), dtype=np.uint8)
        np_array = cv2.imdecode(np_array, flags=1)

        return np_array


    def to_pil(self):
        from PIL import Image
        return Image.fromarray(self.to_numpy())