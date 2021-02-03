import os
import uuid

from stitches_py.resources import field, subfield, subsystem, ss_interface, ss_thread

from CameraConfig import CameraConfig
from CameraFrame import CameraFrame

@subsystem(
    wrapper_image='detector-wrapper'
)
class Camera:
    def __init__(self, config: CameraConfig = None):
        super().__init__()

        import cv2

        pipeline = os.environ.get('CONFIG_GST_PIPELINE', f'v4l2src device=/dev/video0 ! image/raw, width=640, height=480 !  appsink')
        

        print(f'Opening GST pipeline "{pipeline}"')
        self._cam = cv2.VideoCapture('/dev/video0')
        self._current_frame = CameraFrame()


    @ss_interface
    def current_frame(self) -> CameraFrame:
        """
            Current camera frame.
        """
        print(f'Sending frame {self._current_frame}')
        return self._current_frame
        

    @ss_thread
    def _run(self):
        """
            Run camera
        """
        frame_count = 0
        while not self._shutdown_requested:
            ret, frame = self._cam.read()

            if ret:
                if frame is not None:
                    self._current_frame  = CameraFrame.from_numpy(frame)
                    self._current_frame.frame_idx = frame_count
                    self.current_frame()

                    frame_count += 1
                else:
                    print('Frame is empty')
            else:
                print('Error reading frame from camera')
