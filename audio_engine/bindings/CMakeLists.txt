# Try to find pybind11 via package, else fallback to subdirectory
find_package(pybind11 QUIET)
if (NOT pybind11_FOUND)
    message(STATUS "pybind11 not found, using subdirectory")
    include(FetchContent)
    FetchContent_Declare(
        pybind11
        GIT_REPOSITORY https://github.com/pybind/pybind11.git
        GIT_TAG v2.11.1
    )
    FetchContent_MakeAvailable(pybind11)
endif()

pybind11_add_module(audio_engine_py audio_engine_py.cpp)
target_link_libraries(audio_engine_py PRIVATE audio_engine)
