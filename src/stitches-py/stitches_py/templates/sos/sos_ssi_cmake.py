from jinja2 import Template

SOS_SSI_CMAKE_TEMPLATE = Template("""
cmake_minimum_required(VERSION 3.4...3.18)
project({{ ss_name }}HCAL LANGUAGES CXX)

find_package(Protobuf REQUIRED)
find_package(spdlog REQUIRED)

file(GLOB_RECURSE PB_SRC
    "${PROJECT_SOURCE_DIR}/src-gen/protobuf/*.proto"
)

execute_process(
    COMMAND protoc --cpp_out=${PROJECT_SOURCE_DIR}/src-gen --proto_path=${PROJECT_SOURCE_DIR}/src-gen/protobuf ${PB_SRC}
    OUTPUT_VARIABLE PROTOC_OUT
    ERROR_VARIABLE PROTOC_ERR
)

file(GLOB_RECURSE STITCHES_AUTOGEN
    "${PROJECT_SOURCE_DIR}/src-gen/**/*.pb.cc"
)

message(STATUS ${STITCHES_AUTOGEN})


include_directories(
    ${Protobuf_INCLUDE_DIRS}
    ${PROJECT_SOURCE_DIR}/src-gen
    spdlog::spdlog
    $ENV{STITCHES_CAPABILITIES}/AdaptiveInterfaces/ipc_libs/CommonAPI/c++/include
    $ENV{STITCHES_CAPABILITIES}/AdaptiveInterfaces/ipc_libs/posix_named_pipe/c++/1.1/include
    $ENV{STITCHES_CAPABILITIES}/AdaptiveInterfaces/ipc_libs/posix_mqueue/c++/1.1/include
    $ENV{STITCHES_CAPABILITIES}/AdaptiveInterfaces/ipc_libs/zmq/c++/1.1/include
)


add_executable({{ ss_name }}HCAL ${PROJECT_SOURCE_DIR}/src-gen/{{ ss_name }}/Process100/hcal/main.cpp ${STITCHES_AUTOGEN})

target_link_libraries({{ ss_name }}HCAL
    rt
    pthread
    ${Protobuf_LIBRARIES}
    $ENV{STITCHES_CAPABILITIES}/AdaptiveInterfaces/ipc_libs/posix_named_pipe/c++/1.1/libstitches_ipc_posix_named_pipe.a
    $ENV{STITCHES_CAPABILITIES}/AdaptiveInterfaces/ipc_libs/posix_mqueue/c++/1.1/libstitches_ipc_posix_mqueue.a
    $ENV{STITCHES_CAPABILITIES}/AdaptiveInterfaces/ipc_libs/zmq/c++/1.1/libstitches_ipc_zmq.a
)
set_target_properties({{ ss_name }}HCAL PROPERTIES RUNTIME_OUTPUT_DIRECTORY "${PROJECT_SOURCE_DIR}/bin")
""")