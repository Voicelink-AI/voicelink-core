cmake_minimum_required(VERSION 3.14)
project(voicelink_audio_engine)

set(CMAKE_CXX_STANDARD 17)

include_directories(include src)

add_library(audio_engine STATIC
    src/audio_engine.cpp
    src/minimp3.h
    src/minimp3_ex.h
)

# Enable testing
enable_testing()
add_executable(test_audio_engine tests/test_audio_engine.cpp)
target_link_libraries(test_audio_engine audio_engine)

# Prepare for Python bindings (pybind11)
include(FetchContent)
add_subdirectory(bindings)

add_executable(audio_engine_cli src/audio_engine_cli.cpp)
target_link_libraries(audio_engine_cli audio_engine)
