# STITCHES-Py Walkthrough

### [Walkthrough Video](https://aripublic.blob.core.windows.net/files/stitches-py-walkthrough.mp4)

## OVA Setup

Starting from a fresh STITCHES 6R7.2 OVA

1. [Install Docker](https://docs.docker.com/engine/install/centos/) (00:00)
    * `sudo yum install -y yum-utils`
    * `sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo`
    * `sudo yum install -y docker-ce docker-ce-cli containerd.io`
    * `sudo systemctl enable docker`
    * `sudo systemctl start docker`
    * `sudo usermod -aG docker sosite`
2. Log out of VM and log back in. (02:04)
3. Ensure docker is running. (02:50)
    * `docker ps`
4. [Install Docker Compose](https://docs.docker.com/compose/install/) (02:58)
    * `sudo curl -L "https://github.com/docker/compose/releases/download/1.28.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose`
    * `sudo chmod +x /usr/local/bin/docker-compose`
5. Clone code from [GitHub](https://github.com/illinois-ari/stitches-py) (03:22)
    * `git clone https://github.com/illinois-ari/stitches-py.git`
6. Run Setup (03:45)
    * `cd stitches-py`
    * `./scripts/setup`

## Run PingPong Tutorial
1. Register fields with FTG registry (30:27)
    * `./stitches-py --input-dir tutorials/1_pingpong ftg register`
2. List subsystems (30:40)
    * `./stitches-py --input-dir tutorials/1_pingpong ss list`
3. Build all subsystems (30:50)
    * `./stitches-py --input-dir tutorials/1_pingpong ss build`
4. View build output (34:20)
    * `ll build/PingRequester`
5. List SoS (34:40)
    * `./stitches-py --input-dir tutorials/1_pingpong sos list`
6. Build SoS (34:52)
    * `./stitches-py --input-dir tutorials/1_pingpong sos build pingpong.sos.PingPong`
7. Deploy SoS (36:30)
    * `./stitches-py --input-dir tutorials/1_pingpong sos deploy pingpong.sos.PingPong`
8. Inspect running SoS (36:45)
    * `cd build/PingPong`
    * `docker-compose ps`
    * `docker-compose logs ponger`
    * `docker-compose logs ponger-hcal`