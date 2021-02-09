ARG IMAGE_REGISTRY=localhost:5000
FROM ${IMAGE_REGISTRY}/stitches-base
ARG TARGETARCH
ARG ARCHLIB


USER root

RUN apt-get update && \
    DEBIAN_FRONTEND=non-interactive apt-get install -y \
        ant \
        m4 \
        libgcrypt-dev \
        maven \
        wget \
        unzip \
        curl \
        git \
        openjdk-8-jdk \
        psmisc \
        time \
        libxslt-dev \
        libgmp-dev \
        build-essential \
        cmake \
        vim \
        python2.7 \
        python2.7-dev \
        python-pip \
        python3-dev \
        python3-pip \
        python-setuptools \
        python-pyparsing \
        curl \
        wget \
        unzip \
        apt-transport-https \
        ca-certificates \
        curl \
        gnupg-agent \
        software-properties-common

COPY requirements.txt /tmp/requirements.txt
RUN pip3 install -r /tmp/requirements.txt
WORKDIR /tmp
#RUN wget https://bootstrap.pypa.io/get-pip.py && \
#    python2 get-pip.py

RUN wget https://github.com/pybind/pybind11/archive/v2.4.3.tar.gz && \
    tar -xvf v2.4.3.tar.gz && \
    mkdir pybind11-2.4.3/build && \
    cd pybind11-2.4.3/build && \
    cmake .. && make -j `nproc --all` && make install && \
    cd /tmp && rm -rf *

RUN apt-get install -y autoconf libtool

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
    
RUN git clone https://github.com/gabime/spdlog.git && \
    cd spdlog && mkdir build && cd build && \
    cmake .. && make -j && make install && \
    cd /tmp && rm -rf *

RUN update-alternatives --list java && update-alternatives --set java /usr/lib/jvm/java-8-openjdk-$TARGETARCH/jre/bin/java

COPY gradle-4.2-bin.zip /tmp
RUN unzip -d /opt/gradle /tmp/gradle-4.2-bin.zip

ENV GRADLE_HOME=/opt/gradle/gradle-4.2

ENV PATH=${GRADLE_HOME}/bin:${PATH}

WORKDIR /opt

COPY STITCHES_6R7.2_DISTRO-A.tar .
RUN  tar -xvf STITCHES_6R7.2_DISTRO-A.tar && \
    rm STITCHES_6R7.2_DISTRO-A.tar && \
    cd /opt/STITCHES_6R7.2_DISTRO-A && \
    tar xf STITCHES_Capabilities_6R7.2_DISTRO-A.tgz  && \
    tar xf STITCHES_Inputs_6R7.2_DISTRO-A.tgz && \
    tar xf STITCHES_Libraries_6R7.2_DISTRO-A.tgz && \
    rm *.tgz && \
    chown -R sosite:sosite /opt/STITCHES_6R7.2_DISTRO-A




RUN python -m pip install -U  'lxml'
WORKDIR /tmp
RUN git clone git://github.com/zeromq/libzmq.git && \
    cd libzmq && \
    git checkout v4.3.4 && \
    ./autogen.sh && \
    ./configure --prefix=/usr/local --datarootdir=/usr/share && \
    make && \
    sudo make install



USER sosite

WORKDIR /opt/STITCHES_6R7.2_DISTRO-A/STITCHES_Capabilities_6R7.2_DISTRO-A/SysInteg/scripts


# Copy patches 
COPY --chown=sosite:sosite patches/STITCHES_Capabilities_6R7.2_DISTRO-A/ /opt/STITCHES_6R7.2_DISTRO-A/STITCHES_Capabilities_6R7.2_DISTRO-A/


RUN /opt/STITCHES_6R7.2_DISTRO-A/STITCHES_Capabilities_6R7.2_DISTRO-A/SysInteg/scripts/BuildCapabilities.sh && \
    sudo rm -rf /home/sosite/.m2 && \
    sudo rm -rf /home/sosite/.gradle && \
    sudo rm -rf /opt/STITCHES_6R7.2_DISTRO-A/STITCHES_Libraries_6R7.2_DISTRO-A/offline_install && \
    sudo rm -rf /opt/STITCHES_6R7.2_DISTRO-A/STITCHES_Libraries_6R7.2_DISTRO-A/repository && \
    sudo rm -rf /opt/STITCHES_6R7.2_DISTRO-A/STITCHES_Libraries_6R7.2_DISTRO-A/Documentation

RUN cd /tmp && \
    wget https://downloads.sourceforge.net/project/lpsolve/lpsolve/5.5.2.11/lp_solve_5.5.2.11_source.tar.gz && \
    tar -xvf lp_solve_5.5.2.11_source.tar.gz && \
    cd lp_solve_5.5 && \
    sudo chown -R sosite:sosite . && \
    cd lpsolve55 && \
    chmod +x ccc && \
    ./ccc && \
    sudo cp bin/ux64/* $ARCHLIB/ # TODO FIX PLATFORM


ENV JDK_DIR=/usr/lib/jvm/java-8-openjdk-$TARGETARCH
RUN cd /tmp && \
    wget https://downloads.sourceforge.net/project/lpsolve/lpsolve/5.5.2.11/lp_solve_5.5.2.11_java.zip && \
    unzip lp_solve_5.5.2.11_java.zip && \
    cd lp_solve_5.5_java && \
    sudo chown -R sosite:sosite . 

COPY lpsolvej_build.sh /tmp/lp_solve_5.5_java/lib/build
RUN cd /tmp/lp_solve_5.5_java/lib && \
    sudo chmod +x build && \
    ./build && \
    cp /tmp/lp_solve_5.5_java/lib/ux64/liblpsolve55j.so /opt/STITCHES_6R7.2_DISTRO-A/STITCHES_Capabilities_6R7.2_DISTRO-A/STITCHESBinaries/dse/native/ && \
    sudo cp /tmp/lp_solve_5.5_java/lib/ux64/liblpsolve55j.so $ARCHLIB/ # TODO FIX PLATFORM

#$c -fpic $INCL -c $SRC_DIR/lpsolve5j.cpp
