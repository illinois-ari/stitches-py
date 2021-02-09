# STITCHES OVA Setup

Starting from a fresh STITCHES 6R7.2 OVA

1. [Install Docker](https://docs.docker.com/engine/install/centos/)
    * Make sure to run the following after installation
    `sudo usermod -aG docker sosite`
    * Log out of VM and log back in.
2. [Install Docker Compose](https://docs.docker.com/compose/install/)
3. Clone code from [GitHub](https://github.com/illinois-ari/stitches-py)
    * `git clone https://github.com/illinois-ari/stitches-py.git`
4. Run Setup
    * `cd stitches-py && ./scripts/setup`