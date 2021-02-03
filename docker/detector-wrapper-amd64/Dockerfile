ARG WRAPPER_IMAGE=localhost:5000/stitches-wrapper

FROM ${WRAPPER_IMAGE} as dev

FROM nvcr.io/nvidia/cuda:10.2-devel-ubuntu18.04

RUN apt-get update && \
    DEBIAN_FRONTEND=non-interactive apt-get install -y \
        ffmpeg \
        libsm6 \
        libxext6 \
        pkg-config \
        wget \
        build-essential \
        python3-pip \
        python3-dev \
        autoconf \
        libtool

RUN pip3 install torch

# Install protobuf from source to enable fpic
RUN wget https://github.com/protocolbuffers/protobuf/archive/v3.14.0.tar.gz && \
    tar -xvf v3.14.0.tar.gz && \
    cd protobuf-3.14.0 && \
    #git submodule update --init --recursive && \
    ./autogen.sh && ./configure CFLAGS="-fPIC" CXXFLAGS="-fPIC" && \
    make -j `nproc --all` && \
    make install && \
    ldconfig  && \
    cd /tmp && rm -rf *

RUN apt-get install -y git cmake

RUN mkdir /tmp/opencv && \
    cd /tmp/opencv && \
    wget https://github.com/opencv/opencv/archive/3.4.6.tar.gz && \
    tar xf 3.4.6.tar.gz && \
    rm -rf 3.4.6.tar.gz && \
    wget https://github.com/opencv/opencv_contrib/archive/3.4.6.tar.gz && \
    tar xf 3.4.6.tar.gz && \
    rm -rf 3.4.6.tar.gz &&\
    mkdir build && \
    cd build && \
    cmake \
        -DENABLE_CXX11=ON \
        -DOPENCV_EXTRA_MODULES_PATH=../opencv_contrib-3.4.6/modules \
        -DWITH_GSTREAMER=OFF \
        -DBUILD_TESTS=OFF \
        -DBUILD_PERF_TESTS=OFF \
        -DBUILD_EXAMPLES=OFF \
        -DBUILD_opencv_apps=OFF \
        -DBUILD_JAVA=OFF \
        -DBUILD_opencv_python2=OFF \
        -DENABLE_PRECOMPILED_HEADERS=OFF \
        -DCMAKE_INSTALL_PREFIX=/usr \
        ../opencv-3.4.6 && \
    make -j`nproc --all` && \
    make install


RUN python3 -m pip install 'git+https://github.com/facebookresearch/detectron2.git'

RUN pip3 install pytest

RUN wget https://github.com/pybind/pybind11/archive/v2.4.3.tar.gz && \
    tar -xvf v2.4.3.tar.gz && \
    mkdir pybind11-2.4.3/build && \
    cd pybind11-2.4.3/build && \
    cmake .. && make -j `nproc --all` && make install && \
    cd /tmp && rm -rf *


COPY --from=dev /opt/stitches-py /opt/stitches-py

ENV LC_ALL=C.UTF-8 \
    LANG=C.UTF-8 \
    PYTHONPATH=$PYTHONPATH:/opt/stitches-py/lib