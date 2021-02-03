from stitches_py.resources import system_of_systems, sos_subsystem, sos_connection

from Camera import Camera
from CameraFrame import CameraFrame
from Recorder import Recorder
from Detector import Detector

@system_of_systems()
class ObjectDetectionSoS:
    """
    Simple camera streaming application
    """

    @sos_subsystem(
        devices=['/dev/video0'],
        extra_volumes=[
            '/usr/lib/gstreamer-1.0:/usr/lib/gstreamer-1.0',
            '/usr/lib/aarch64-linux-gnu/gstreamer-1.0:/usr/lib/aarch64-linux-gnu/gstreamer-1.0'
        ]
    )
    def camera(self) -> Camera:
        """ Camera to stream """
        pass


    @sos_subsystem(
        gpu_enabled=True
    )
    def detector(self) -> Detector:
        """ Object detector """
        pass

    @sos_subsystem(
        extra_volumes=[
            '$PWD/out:/out'
        ]
    )
    def recorder(self) -> Recorder:
        """ Record detector output """
        pass


    @sos_connection('camera', 'current_frame', 'detector', 'detect_frame')
    def frame_to_detector(self, msg: CameraFrame) -> CameraFrame:
        """ Route frames from camera to detector. """
        pass


    @sos_connection('detector', 'detect_frame', 'recorder', 'record_frame')
    def detector_to_recorder(self, msg: CameraFrame) -> CameraFrame:
        """ Route frames from detector to recorder. """
        pass

    
