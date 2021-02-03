# stitches-py
Python bindings for the DARPA STITCHES middleware.

## Getting Started

### Requirements
* [docker](https://docs.docker.com/get-docker/)
* [docker-compose](https://docs.docker.com/compose/install/)

Validated Platforms:
* Ubuntu Linux
* Windows 10 (requires [WSL2](https://docs.microsoft.com/en-us/windows/wsl/install-win10))
* MacOS


To get started using `stitches-py` first set up a development environment by running:

```bash
./scripts/setup # Setup development environment. Rerun if changes are made to Docker image to refresh dev service.
```

This script will perform a series of tasks including:
1. Starting a local Docker registry.
2. Building the development images.
3. Starting a local FTGRepo instance.
4. Launching the development service.

All subsequent development tasks run inside the development service container which has access to the project directory via volume mount.

To run commands inside the development container, you may utilize the provided wrapper script.

```bash
./scripts/dev [CMD] # Run a command inside the development service container.
./scripts/dev bash # Drop into a bash shell.
```

### stitches-cli
A command line interface is available.

```bash
./stitches-py --help
```


### Tutorials
1. [Ping Pong](tutorials/1_pingpong/README.md)
2. [Object Detection](tutorials/2_object_detector/README.md)