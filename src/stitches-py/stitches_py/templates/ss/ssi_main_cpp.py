from jinja2 import Template

SSI_MAIN_TEMPLATE = Template("""
#include <pybind11/embed.h>
#include <pybind11/stl.h>
#include <iostream>
#include "spdlog/spdlog.h"
#include "spdlog/sinks/stdout_color_sinks.h"

#include <{{ ss_name }}SSIUpper.cpp>

namespace py = pybind11;
using namespace py::literals;

void segfault_sigaction(int signal, siginfo_t *si, void *arg)
{
    spdlog::error("Caught segfault at address {}", si->si_addr);
    exit(1);
}


int main(int argc, char *argv[]) {
    auto logger = spdlog::stdout_color_mt("{{ ss_name }}");
    logger->set_level(spdlog::level::debug); // Set global log level to debug
    logger->set_pattern("[%H:%M:%S %z] [%n] [%^---%L---%$] [thread %t] %v");
    spdlog::set_default_logger(logger);

    struct sigaction sa;

    memset(&sa, 0, sizeof(struct sigaction));
    sigemptyset(&sa.sa_mask);
    sa.sa_sigaction = segfault_sigaction;
    sa.sa_flags   = SA_SIGINFO;

    //sigaction(SIGSEGV, &sa, NULL);

    {{ ss_mod }}::{{ ss_name }}::SSI::{{ ss_name }}SSIUpper* ssiUpper;

    spdlog::info("Starting Python Interpreter");
    py::scoped_interpreter guard{};
    auto gil_state = PyGILState_Ensure();
    {
        spdlog::info("Importing SSI module");
        py::module ssPyMod = py::module::import("{{ ss._RESOURCE_PATH }}");

        spdlog::info("Instantiating SSI class");
        py::object ssPyCls = ssPyMod.attr("{{ ss_name }}").cast<py::object>();
        py::object ssPyObj = ssPyCls();
    

        spdlog::info("Initializing SSI upper");
        ssiUpper = new {{ ss_mod }}::{{ ss_name }}::SSI::{{ ss_name }}SSIUpper(ssPyObj);
    }
    bool initSuccess = ssiUpper->init();

    if (!initSuccess) {
        spdlog::error("Error initing ssiUpper");
    }

    spdlog::info("Running SSI");
    ssiUpper->run();
}
""")