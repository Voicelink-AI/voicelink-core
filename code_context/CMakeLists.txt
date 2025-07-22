cmake_minimum_required(VERSION 3.14)
project(voicelink_code_context)

set(CMAKE_CXX_STANDARD 17)

include_directories(include)

add_library(code_context STATIC
    src/code_parser.cpp
)

enable_testing()
add_executable(test_code_parser tests/test_code_parser.cpp)
target_link_libraries(test_code_parser code_context)
add_test(NAME CodeParserTest COMMAND test_code_parser)

add_executable(code_context_cli src/code_context_cli.cpp)
target_link_libraries(code_context_cli code_context)
