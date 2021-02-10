# STITCHES-Py Walkthrough

## OVA Setup

Starting from a fresh STITCHES 6R7.2 OVA

1. [Install Docker](https://docs.docker.com/engine/install/centos/)
    * `sudo yum install -y yum-utils`
    * `sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo`
    * `sudo yum install -y docker-ce docker-ce-cli containerd.io`
    * `sudo systemctl enable docker`
    * `sudo systemctl start docker`
    * `sudo usermod -aG docker sosite`
2. Log out of VM and log back in.
3. Ensure docker is running.
    * `docker ps`
4. [Install Docker Compose](https://docs.docker.com/compose/install/)
    * `sudo curl -L "https://github.com/docker/compose/releases/download/1.28.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose`
    * `sudo chmod +x /usr/local/bin/docker-compose`
5. Clone code from [GitHub](https://github.com/illinois-ari/stitches-py)
    * `git clone https://github.com/illinois-ari/stitches-py.git`
6. Run Setup
    * `cd stitches-py`
    * `./scripts/setup`

## Run PingPong Tutorial
1. Register fields with FTG registry
    * `./stitches-py --input-dir tutorials/1_pingpong ftg register`
2. List subsystems
    * `./stitches-py --input-dir tutorials/1_pingpong ss list`
3. Build all subsystems
    * `./stitches-py --input-dir tutorials/1_pingpong ss build`
4. View build output
    * `ll build/PingRequester`
5. List SoS
    * `./stitches-py --input-dir tutorials/1_pingpong sos list`
6. Build SoS
    * `./stitches-py --input-dir tutorials/1_pingpong sos build pingpong.sos.PingPong`
7. Deploy SoS
    * `./stitches-py --input-dir tutorials/1_pingpong sos deploy pingpong.sos.PingPong`
8. Inspect running SoS
    * `cd build/PingPong`
    * `docker-compose ps`
    * `docker-compose logs ponger`
    * `docker-compose logs ponger-hcal`