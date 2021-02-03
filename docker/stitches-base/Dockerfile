ARG BASE_TAG=bionic
FROM ubuntu:$BASE_TAG

RUN apt-get update && \
    apt-get install -y \
        sudo

RUN useradd -ms /bin/bash sosite && \
    echo "ALL ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers && \
    mkdir /opt/stitches-py && \
    chown sosite /opt/stitches-py

USER sosite

ENV STITCHES_HOME=/opt/STITCHES_6R7.2_DISTRO-A
ENV STITCHES_INPUTS=${STITCHES_HOME}/STITCHES_Inputs_6R7.2_DISTRO-A \
    STITCHES_LIBRARIES=${STITCHES_HOME}/STITCHES_Libraries_6R7.2_DISTRO-A \
    STITCHES_CAPABILITIES=${STITCHES_HOME}/STITCHES_Capabilities_6R7.2_DISTRO-A
ENV STITCHES_BINARIES=${STITCHES_CAPABILITIES}/STITCHESBinaries \
    STITCHES_MVN_REPO=${STITCHES_LIBRARIES}/repository \
    STITCHES_NOREPLACE_REPO=${STITCHES_LIBRARIES}/repository_noreplace \
    STITCHES_PLUGIN_REPO=${STITCHES_LIBRARIES}/repository