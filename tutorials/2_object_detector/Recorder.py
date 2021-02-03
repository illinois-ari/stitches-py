import os
import time
import uuid

from stitches_py.resources import field, subfield, subsystem, ss_interface, ss_thread

from CameraFrame import CameraFrame

@subsystem(
    wrapper_image='detector-wrapper'
)
class Recorder:
    def __init__(self):
        super().__init__()
        import cv2

        self._width = int(os.environ.get('CONFIG_RECORDER_WIDTH', '640'))
        self._height = int(os.environ.get('CONFIG_RECORDER_HEIGHT', '480'))
        self._fps = float(os.environ.get('CONFIG_RECORDER_FPS', '30'))
        self._fourcc = cv2.VideoWriter_fourcc(*'MJPG')
            

        self._out_path = os.environ.get('CONFIG_RECORDER_OUT_PATH', '/out')
        self._max_frames = int(os.environ.get('CONFIG_RECORDER_MAX_FRAMES', '600'))
        self._frame_count = 0

        self._writer = None



    def _open_writer(self):
        import cv2
        out_file = os.path.join(self._out_path, f'record-{int(self._frame_count/self._max_frames)}.mp4')
        print(f'Opening out file at {out_file}')
        self._writer = cv2.VideoWriter(out_file, self._fourcc, self._fps, (self._width, self._height))


    @ss_interface
    def record_frame(self, frame: CameraFrame):
        """
            Record a camera frame
        """
        f = frame.to_numpy()
        
        self._writer.write(f)

        self._frame_count += 1
        print(f'Writing frame {self._frame_count} {f.shape}')

        if (self._frame_count % self._max_frames == 0):
            print(f'Rolling over file')
            self._writer.release()
            self._open_writer()
        

    @ss_thread
    def _run(self):
        """
            Run streamer
        """
        self._open_writer()
        while not self._shutdown_requested:
            time.sleep(1)
