from jinja2 import Template

SSI_PYBIND_TEMPLATE = Template("""
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/iostream.h>

#include <{{ ss_name }}SSIUpper.cpp>

namespace py = pybind11;



PYBIND11_MODULE({{ ss_name }}Ext, m) {
    m.doc() = "STITCHES SSI Interface for {{ ss_name }} Service";

    py::class_<{{ ss_mod }}::{{ ss_name }}::SSI::{{ ss_name }}SSIUpper>(m, "{{ ss_name }}SSIUpper")
        .def(py::init<py::object>())
        .def("init", &{{ ss_mod }}::{{ ss_name }}::SSI::{{ ss_name }}SSIUpper::init)
        .def("run", &{{ ss_mod }}::{{ ss_name }}::SSI::{{ ss_name }}SSIUpper::run);

    py::add_ostream_redirect(m, "ostream_redirect");

    {% for f in ss._INTERFACE_FIELDS %}
        py::class_<{{ field_to_c(f) }}>(m, "{{ f._RESOURCE_NAME }}")
        .def(py::init<>())
        .def_static("from_py",
            [](const py::object &obj) {
               {{ field_to_c(f) }} cField = {{ field_to_c(f) }}();
               
                {% for sf in f._SUB_FIELDS %}
                cField.m{{ to_camel(sf.name) }} = obj.attr("{{ sf.name }}").cast<{{ type_to_c(sf.field_type.type) }}>();
                {% endfor %}
                return cField;

            }
        )
        ;
        
    {% endfor %}
}


""")