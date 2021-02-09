# STITCHES OVA Setup

Starting from a fresh STITCHES 6R7.2 OVA

1. [Install Docker](https://docs.docker.com/engine/install/centos/)
    * `sudo yum install -y yum-utils`
    * `sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo`
    * `sudo yum install docker-ce docker-ce-cli containerd.io`
    * `sudo systemctl enable docker`
    * `sudo systemctl start docker`
    * `sudo usermod -aG docker sosite`
2. Log out of VM and log back in.
    * Ensure docker is running. `docker ps`
2. [Install Docker Compose](https://docs.docker.com/compose/install/)
    * `sudo curl -L "https://github.com/docker/compose/releases/download/1.28.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose`
    * `sudo chmod +x /usr/local/bin/docker-compose`
3. Clone code from [GitHub](https://github.com/illinois-ari/stitches-py)
    * `git clone https://github.com/illinois-ari/stitches-py.git`
4. Run Setup
    * `cd stitches-py`
    * `./scripts/setup`