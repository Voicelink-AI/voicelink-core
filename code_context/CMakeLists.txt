cmake_minimum_required(VERSION 3.14)
project(voicelink_code_context)

set(CMAKE_CXX_STANDARD 17)

# Include directories
include_directories(include)

# Source files
set(SOURCES
    src/code_parser.cpp
)

# Create the library
add_library(code_context ${SOURCES})

# Create CLI executable 
add_executable(code_context_cli src/code_parser.cpp)
target_compile_definitions(code_context_cli PRIVATE BUILD_CLI)

# Try to find and build Python bindings if pybind11 is available
find_package(pybind11 QUIET)

if(pybind11_FOUND)
    message(STATUS "pybind11 found - building Python bindings")
    
    # Create Python bindings
    pybind11_add_module(code_parser_py bindings/code_parser_py.cpp ${SOURCES})
    
    # Set properties
    set_target_properties(code_parser_py PROPERTIES
        CXX_VISIBILITY_PRESET "hidden"
        VISIBILITY_INLINES_HIDDEN ON
    )
else()
    message(WARNING "pybind11 not found - skipping Python bindings")
    message(STATUS "To build Python bindings, install pybind11:")
    message(STATUS "  pip install pybind11[global]")
    message(STATUS "  or conda install pybind11")
endif()

# Link libraries for CLI
target_link_libraries(code_context_cli)
