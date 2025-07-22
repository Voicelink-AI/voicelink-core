#include "code_parser.h"
#include <iostream>

int main() {
    voicelink::code::CodeParser parser;
    auto symbols = parser.scan_file("example.py"); // example.cpp
    for (const auto& sym : symbols) {
        std::cout << sym.type << " " << sym.name << " at line " << sym.line << "\n";
    }
    return 0;
}
