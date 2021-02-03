from jinja2 import Template

HCAL_CMAKE_TEMPLATE = Template("""
cmake_minimum_required(VERSION 3.4...3.18)
project({{ sos_name }}HCAL LANGUAGES CXX)
SET( CMAKE_BUILD_TYPE Debug )

find_package(Protobuf REQUIRED)


file(GLOB_RECURSE STITCHES_AUTOGEN
    "${PROJECT_SOURCE_DIR}/src-gen/*.cc"
)

file(GLOB_RECURSE PB_SRC
    "${PROJECT_SOURCE_DIR}/src-gen/protobuf/*.proto"
)


execute_process(
    COMMAND protoc --cpp_out=${PROJECT_SOURCE_DIR}/src-gen --proto_path=${PROJECT_SOURCE_DIR}/src-gen/protobuf ${PB_SRC}
    OUTPUT_VARIABLE PROTOC_OUT
    ERROR_VARIABLE PROTOC_ERR
)


include_directories(
    ${Protobuf_INCLUDE_DIRS}
    ${PROJECT_SOURCE_DIR}/src-gen
    $ENV{STITCHES_CAPABILITIES}/AdaptiveInterfaces/ipc_libs/CommonAPI/c++/include
    $ENV{STITCHES_CAPABILITIES}/AdaptiveInterfaces/ipc_libs/posix_named_pipe/c++/1.1/include
    $ENV{STITCHES_CAPABILITIES}/AdaptiveInterfaces/ipc_libs/posix_mqueue/c++/1.1/include
    $ENV{STITCHES_CAPABILITIES}/AdaptiveInterfaces/ipc_libs/zmq/c++/1.1/include
)

""")