import os
import uuid
import time

from stitches_py.resources import field, subfield, subsystem, ss_interface, ss_thread

from DetectorConfig import DetectorConfig
from CameraFrame import CameraFrame

COCO_INSTANCE_CATEGORY_NAMES = [
    '__background__', 'person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus',
    'train', 'truck', 'boat', 'traffic light', 'fire hydrant', 'N/A', 'stop sign',
    'parking meter', 'bench', 'bird', 'cat', 'dog', 'horse', 'sheep', 'cow',
    'elephant', 'bear', 'zebra', 'giraffe', 'N/A', 'backpack', 'umbrella', 'N/A', 'N/A',
    'handbag', 'tie', 'suitcase', 'frisbee', 'skis', 'snowboard', 'sports ball',
    'kite', 'baseball bat', 'baseball glove', 'skateboard', 'surfboard', 'tennis racket',
    'bottle', 'N/A', 'wine glass', 'cup', 'fork', 'knife', 'spoon', 'bowl',
    'banana', 'apple', 'sandwich', 'orange', 'broccoli', 'carrot', 'hot dog', 'pizza',
    'donut', 'cake', 'chair', 'couch', 'potted plant', 'bed', 'N/A', 'dining table',
    'N/A', 'N/A', 'toilet', 'N/A', 'tv', 'laptop', 'mouse', 'remote', 'keyboard', 'cell phone',
    'microwave', 'oven', 'toaster', 'sink', 'refrigerator', 'N/A', 'book',
    'clock', 'vase', 'scissors', 'teddy bear', 'hair drier', 'toothbrush'
]


@subsystem(
    wrapper_image='detector-wrapper'
)
class Detector:
    def __init__(self, config: DetectorConfig = None):
        super().__init__()

        import torch
        import torchvision.models as models

        self._device = torch.device('cuda')
        print(f'Using device {self._device}')
        self._model = models.detection.fasterrcnn_resnet50_fpn(pretrained=True)
        self._model.eval()
        self._model.to(self._device)

        self._sample_rate = int(os.environ.get('CONFIG_SAMPLE_RATE', '10'))


    @ss_interface
    def detect_frame(self, frame: CameraFrame) -> CameraFrame:
        """
            Detect objects in a camera frame
        """
        from torchvision.transforms import ToTensor, ToPILImage
        from PIL import Image, ImageDraw, ImageFont

        out_f = None

        if (frame.frame_idx % self._sample_rate == 0):
            print(f'Detecting objects in frame {frame.frame_idx}')

            frame_img = frame.to_pil()

            in_tensor = ToTensor()(frame_img).unsqueeze(0).to(self._device)

            predictions = self._model(in_tensor)[0]

            draw = ImageDraw.Draw(frame_img)
            txt_font = ImageFont.load_default()
            fill_color = (255, 255, 255, 100)
            color = (65, 255, 0, 100)

            for i, score in enumerate(predictions['scores']):
                if score > .75:
                    bbox = predictions['boxes'][i]
                    label = COCO_INSTANCE_CATEGORY_NAMES[predictions['labels'][i]]
                    
                    draw.rectangle(bbox.tolist(), width=1, outline=color)
                    draw.text((bbox[0], bbox[1]), label, fill=color, font=txt_font)
                    


            out_f = CameraFrame.from_pil(frame_img)

        return out_f
        

    @ss_thread
    def _run(self):
        """
            Run detector
        """
        while not self._shutdown_requested:
            time.sleep(.1)
