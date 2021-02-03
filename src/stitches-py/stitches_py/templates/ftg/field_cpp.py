from jinja2 import Template

FIELD_CPP_TEMPLATE = Template(
#include <string>
#include <mil/darpa/sosite/stitches/stitcheslib>
#include <pybind11/pybind11.h>
#include <{{ f_mod }}/ftg/{{ f_name }}.hpp>

namespace py = pybind11;

namespace {{ f_mod }} {
namespace ftg {
class {{ f_name }Py {
  public:
    {{ ss_name }}SSIUpper(py::object pySS)
     : SSIUpper() {
        wrappedCls = pySS;
        wrappedCls.attr("_int_cb") = py::cpp_function(
          [&](std::string intName, py::object intOut) {
              {% for out_int in out_ints %}
                if (intName == "{{out_int.method.__name__}}") {
                  std::shared_ptr<{{ field_to_c(out_int.type) }}> msgPtr = std::make_shared<{{ field_to_c(out_int.type) }}>(intOut);
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

    {% for out_int in out_ints %}
        bool wrapped_send_{{ out_int.name }}(const {{ field_to_c(out_int.type) }}& msg) {
            std::shared_ptr<{{ field_to_c(out_int.type) }}> msgPtr = std::make_shared<{{ field_to_c(out_int.type) }}>(msg);
            return this->send_{{ out_int.name }}(msgPtr);
        }

    {% endfor %}

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
          this->cbFunc = cbFunc;
        }
      
      
        // Method invoked by SSI Mid upon receipt of STITCHES message 
        bool process( mil::darpa::sosite::stitches::StitchesPtr< {{ i_type._RESOURCE_MODULE }}::{{ i_type._RESOURCE_GROUP }}::{{ i_type._RESOURCE_NAME }} > stitches_msg ) {
          this->cbFunc(stitches_msg);
          
          return true;
        }
      
      protected:
        py::function cbFunc;
    };

    {{ i_name }}::{{ i_name }}CallbackInterface* instantiate{{ i_name }}CallbackInterface() {
        py::print("Instantiating callback for interface {{ i_name }}");
        py::function cbFunc = (py::function)this->wrappedCls.attr("{{ in_int.method.__name__ }}");
        {{ i_name }}CallbackInterfaceImpl cbInterface = {{ i_name }}CallbackInterfaceImpl(cbFunc);
        return ({{ ss_mod }}::{{ ss_name }}::SSI::{{ i_name }}::{{ i_name }}CallbackInterface*)&cbInterface;
    };

    {% endfor %}

};
}
}
}
""")