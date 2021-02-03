from jinja2 import Template

SSI_UPPER_TEMPLATE = Template("""
#include <string>
#include <mil/darpa/sosite/stitches/stitcheslib>
#include <pybind11/pybind11.h>
#include <pybind11/embed.h>
#include "spdlog/spdlog.h"
#include <{{ ss_mod }}/{{ ss_name }}/SSI/SSIMid.hpp>
#include <{{ ss_mod }}/{{ ss_name }}/SSI/SSIUpper.hpp>

// TODO: Include files for each interface
{% for in_int in in_ints %}
{% set i_name=in_int.name %}
#include <{{ ss_mod }}/{{ ss_name }}/SSI/{{ i_name }}/{{ i_name }}CallbackInterface.hpp>
{% endfor %}

namespace py = pybind11;
using namespace py::literals;

namespace {{ ss_mod }} {
namespace {{ ss_name }} {
namespace SSI {

{% for f in ss_fields %}
inline std::shared_ptr<{{ f._RESOURCE_MODULE}}::ftg::{{ f._RESOURCE_NAME }}> {{ f._RESOURCE_NAME }}FromPy(py::object pyObj) {
  std::shared_ptr<{{ f._RESOURCE_MODULE}}::ftg::{{ f._RESOURCE_NAME }}> outMsg = std::make_shared<{{ f._RESOURCE_MODULE}}::ftg::{{ f._RESOURCE_NAME }}>();
  {%- for sf in f._SUB_FIELDS %}
  outMsg->m{{ to_camel(sf.name) }} = pyObj.attr("{{ sf.name }}").cast<{{ type_to_c(sf.field_type.type) }}>();
  {% endfor -%}
  return outMsg;
};
{% endfor %}

{% for f in ss_fields %}
inline py::object {{ f._RESOURCE_NAME }}ToPy(std::shared_ptr<{{ f._RESOURCE_MODULE}}::ftg::{{ f._RESOURCE_NAME }}> sMsg) {
  spdlog::debug("Loading Field module {{ f._RESOURCE_NAME }}");
  py::object pyField;
  auto gil_state = PyGILState_Ensure();
  {
    py::module fieldMod = py::module::import("{{ f._RESOURCE_NAME }}");
    spdlog::debug("Loading Field class {{ f._RESOURCE_NAME }}");
    py::object fieldCls = fieldMod.attr("{{ f._RESOURCE_NAME }}");
    pyField = fieldCls();

    {%- for sf in f._SUB_FIELDS %}
        pyField.attr("{{ sf.name }}") = py::cast(sMsg->m{{ to_camel(sf.name) }});
    {% endfor -%}
  }
  PyGILState_Release(gil_state);

  return pyField;
};
{% endfor %}
  
class {{ ss_name }}SSIUpper : public SSIUpper {
  public:
    {{ ss_name }}SSIUpper(py::object pySS)
     : SSIUpper() {
        wrappedCls = pySS;
        // this->wrappedCls.attr("init")();
        wrappedCls.attr("_int_cb") = py::cpp_function(
          [&](std::string intName, py::object intOut) {
              {% for out_int in out_ints %}
                if (intName == "{{out_int.name}}") {
                  std::shared_ptr<{{ field_to_c(out_int.type) }}> msgPtr = {{ out_int.type._RESOURCE_NAME}}FromPy(intOut);
                  //spdlog::debug("{}", *msgPtr);
                  send_{{ out_int.name }}(msgPtr);
                }
              {% endfor %}
          }
        );
    }

    ~{{ ss_name }}SSIUpper() {
    }

    void run() {
      this->wrappedCls.attr("run")();
    }


  protected:

    py::object wrappedCls;
  
    void bindToCore() {

    }


    {% for in_int in in_ints %}
    {% set i_name=in_int.name %}
    {% set i_type=in_int.type  %}


    class {{ i_name }}CallbackInterfaceImpl : public {{ i_name }}::{{ i_name }}CallbackInterface {
      public:
        {{ i_name }}CallbackInterfaceImpl (py::function cbFunc) {
          spdlog::debug("Binding Python callback {}", (void*)&cbFunc);
          this->cbFunc = cbFunc;
        }
      
      
        // Method invoked by SSI Mid upon receipt of STITCHES message 
        bool process( mil::darpa::sosite::stitches::StitchesPtr< {{ i_type._RESOURCE_MODULE }}::{{ i_type._RESOURCE_GROUP }}::{{ i_type._RESOURCE_NAME }} > stitches_msg ) {
          spdlog::debug("Converting message to Python");
          auto gil_state = PyGILState_Ensure();
          {
          convertedObj = {{ i_type._RESOURCE_NAME }}ToPy(stitches_msg);
          spdlog::debug("Invoking callback with py object object");
            this->cbFunc(convertedObj);
          }
          PyGILState_Release(gil_state);
          return true;
        }
      
      protected:
        py::function cbFunc;
        py::object convertedObj;
    };

    {{ i_name }}CallbackInterfaceImpl* {{ i_name }}Cb;

    {{ i_name }}::{{ i_name }}CallbackInterface* instantiate{{ i_name }}CallbackInterface() {
        spdlog::info("Instantiating callback for interface {{ i_name }}");
        py::function cbFunc = (py::function)this->wrappedCls.attr("{{ in_int.method.__name__ }}");
        {{ i_name }}Cb =  new {{ i_name }}CallbackInterfaceImpl(cbFunc);
        spdlog::info("Done instantiating callback for interface {{ i_name }} {}", (void*){{ i_name }}Cb);
        return ({{ ss_mod }}::{{ ss_name }}::SSI::{{ i_name }}::{{ i_name }}CallbackInterface*) {{ i_name }}Cb;
    };

    {% endfor %}

};
}
}
}
""")