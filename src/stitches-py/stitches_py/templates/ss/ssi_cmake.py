from jinja2 import Template

SSI_CMAKE_TEMPLATE = Template("""
cmake_minimum_required(VERSION 3.4...3.18)
project({{ ss_name }} LANGUAGES CXX)

SET( CMAKE_BUILD_TYPE Debug )

execute_process(COMMAND uname -s OUTPUT_VARIABLE OS)
execute_process(COMMAND uname -m OUTPUT_VARIABLE ARCH)

find_package(PkgConfig REQUIRED) 
find_package(pybind11 REQUIRED)
find_package(Protobuf REQUIRED)
find_package(spdlog REQUIRED)

pkg_check_modules(PYTHON REQUIRED IMPORTED_TARGET python3)



file(GLOB_RECURSE STITCHES_AUTOGEN 
    "${PROJECT_SOURCE_DIR}/Stitches/auto-gen/ssi/*.cc"
)

file(GLOB_RECURSE PROTO_AUTOGEN 
    "${PROJECT_SOURCE_DIR}/Stitches/auto-gen/gpb/**/*.pb.cc"
)

add_library({{ ss_name }}Proto STATIC ${PROTO_AUTOGEN})
set_target_properties({{ ss_name }}Proto PROPERTIES POSITION_INDEPENDENT_CODE TRUE)

target_link_libraries({{ ss_name }}Proto
    rt
    pthread
    ${Protobuf_LIBRARIES}
)

# add_library({{ ss_name }}SSI STATIC ${STITCHES_AUTOGEN})
# set_target_properties({{ ss_name }}SSI PROPERTIES POSITION_INDEPENDENT_CODE TRUE)

# target_link_libraries({{ ss_name }}SSI
#    {{ ss_name }}Proto
#    rt
#    pthread
#    spdlog::spdlog
#    ${Protobuf_LIBRARIES}
#    $ENV{STITCHES_CAPABILITIES}/AdaptiveInterfaces/ipc_libs/posix_named_pipe/c++/1.1/libstitches_ipc_posix_named_pipe.a
#    $ENV{STITCHES_CAPABILITIES}/AdaptiveInterfaces/ipc_libs/posix_mqueue/c++/1.1/libstitches_ipc_posix_mqueue.a
# )



include_directories(
    ${Protobuf_INCLUDE_DIRS}
    PkgConfig::PYTHON
    ${PROJECT_SOURCE_DIR}/Stitches/auto-gen/ssi
    ${PROJECT_SOURCE_DIR}/Stitches/auto-gen/gpb
    ${PROJECT_SOURCE_DIR}/Stitches/src
    $ENV{STITCHES_CAPABILITIES}/AdaptiveInterfaces/ipc_libs/CommonAPI/c++/include
    $ENV{STITCHES_CAPABILITIES}/AdaptiveInterfaces/ipc_libs/posix_named_pipe/c++/1.1/include
    $ENV{STITCHES_CAPABILITIES}/AdaptiveInterfaces/ipc_libs/posix_mqueue/c++/1.1/include
)

file(GLOB_RECURSE SSI_SRC
    "${PROJECT_SOURCE_DIR}/Stitches/src/*.cpp"
)

pybind11_add_module({{ ss_name }}Ext ${SSI_SRC})

target_link_libraries({{ ss_name }}Ext PRIVATE
#    {{ ss_name }}SSI
    {{ ss_name }}Proto
    rt
    pthread
    ${Protobuf_LIBRARIES}
    $ENV{STITCHES_CAPABILITIES}/AdaptiveInterfaces/ipc_libs/posix_named_pipe/c++/1.1/libstitches_ipc_posix_named_pipe.a
    $ENV{STITCHES_CAPABILITIES}/AdaptiveInterfaces/ipc_libs/posix_mqueue/c++/1.1/libstitches_ipc_posix_mqueue.a
)

add_executable({{ ss_name }} ${SSI_SRC})


target_link_libraries({{ ss_name }}
#    {{ ss_name }}SSI
    {{ ss_name }}Proto
    rt
    pthread
    ${Protobuf_LIBRARIES}
    PkgConfig::PYTHON
    $ENV{STITCHES_CAPABILITIES}/AdaptiveInterfaces/ipc_libs/posix_named_pipe/c++/1.1/libstitches_ipc_posix_named_pipe.a
    $ENV{STITCHES_CAPABILITIES}/AdaptiveInterfaces/ipc_libs/posix_mqueue/c++/1.1/libstitches_ipc_posix_mqueue.a
)


# set_target_properties({{ ss_name }}SSI PROPERTIES LIBRARY_OUTPUT_DIRECTORY "${PROJECT_SOURCE_DIR}/bin")
set_target_properties({{ ss_name }}Ext PROPERTIES LIBRARY_OUTPUT_DIRECTORY "${PROJECT_SOURCE_DIR}/bin")
set_target_properties({{ ss_name }} PROPERTIES RUNTIME_OUTPUT_DIRECTORY "${PROJECT_SOURCE_DIR}/bin")
""")