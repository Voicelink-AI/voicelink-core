#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include "code_parser.h"

namespace py = pybind11;

PYBIND11_MODULE(code_parser_py, m) {
    py::class_<voicelink::code::CodeSymbol>(m, "CodeSymbol")
        .def_readwrite("type", &voicelink::code::CodeSymbol::type)
        .def_readwrite("name", &voicelink::code::CodeSymbol::name)
        .def_readwrite("line", &voicelink::code::CodeSymbol::line);

    py::class_<voicelink::code::CodeParser>(m, "CodeParser")
        .def(py::init<>())
        .def("scan_file", &voicelink::code::CodeParser::scan_file)
        .def("detect_language", &voicelink::code::CodeParser::detect_language);
}
