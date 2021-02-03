ARG IMAGE_REGISTRY=localhost:5000
FROM ${IMAGE_REGISTRY}/stitches-capabilities
ARG TARGETARCH
USER root

COPY requirements.txt /tmp/requirements.txt

RUN mkdir -p /opt/stitches-py/lib && \
    pip3 install -t /opt/stitches-py/lib -r /tmp/requirements.txt && \
    chown -R sosite:sosite /opt/stitches-py 

    
RUN curl -fsSL https://download.docker.com/linux/ubuntu/gpg | apt-key add - && \
    add-apt-repository \
      "deb [arch=$TARGETARCH] https://download.docker.com/linux/ubuntu \
      $(lsb_release -cs) \
      stable" && \
    apt-get update && \
    apt-get install -y docker-ce-cli binfmt-support qemu-user-static && \
    groupadd --gid 999 docker && \
    usermod -a -G docker sosite && \
    mkdir -p ~/.docker/cli-plugins && \
    curl -s https://api.github.com/repos/docker/buildx/releases/latest | \
        grep "browser_download_url.*linux-amd64" | cut -d : -f 2,3 | tr -d \" | \
    xargs curl -L -o ~/.docker/cli-plugins/docker-buildx && \
    chmod a+x ~/.docker/cli-plugins/docker-buildx && \
    curl -L "https://github.com/docker/compose/releases/download/1.27.4/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose && \
    chmod +x /usr/local/bin/docker-compose

USER sosite

ENV LC_ALL=C.UTF-8 \
    LANG=C.UTF-8 \ 
    PYTHONPATH=$PYTHONPATH:/usr/local/lib/python3.6/dist-packages:/opt/stitches-py/lib