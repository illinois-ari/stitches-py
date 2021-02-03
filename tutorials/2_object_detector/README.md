# Object Detector

In this tutorial we will create a SoS that will detect objects from a camera and output the resulting annotated image to a video file.


#### TLDR
To run this tutorial

```bash
./stitches-py --input-dir tutorials/2_object_detector ftg register
./stitches-py --input-dir examples/2_object_detector ss build
./stitches-py --input-dir examples/2_object_detector sos build objectdetectionsos.sos.ObjectDetectionSoS
cd build/ObjectDetectionSoS
docker-compose up -d
```

Recorded videos will be saved to the `out` directory in that path.

[![STITCHES Demo](stiches-demo.gif)]