#include "code_parser.h"
#include <fstream>
#include <regex>
#include <sstream>
#include <iostream>
#include <filesystem>

namespace voicelink {
namespace code {

std::string CodeParser::detect_language(const std::string& file_path) {
    auto ext = std::filesystem::path(file_path).extension().string();
    if (ext == ".py") return "python";
    if (ext == ".cpp" || ext == ".cc" || ext == ".hpp" || ext == ".h") return "cpp";
    if (ext == ".js") return "javascript";
    if (ext == ".c") return "c";
    return "unknown";
}

std::vector<CodeSymbol> CodeParser::scan_file(const std::string& file_path) {
    std::vector<CodeSymbol> symbols;
    std::ifstream file(file_path);
    if (!file) return symbols;

    std::string line;
    int lineno = 0;

    std::regex py_func(R"(^\s*def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\()");
    std::regex py_class(R"(^\s*class\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*[\(:])");

    std::regex cpp_func(R"(^\s*[a-zA-Z_][a-zA-Z0-9_:<>]*\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\()");
    std::regex cpp_class(R"(^\s*class\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*[\{:])");

    std::string lang = detect_language(file_path);

    while (std::getline(file, line)) {
        ++lineno;
        std::smatch match;
        if (lang == "python") {
            if (std::regex_search(line, match, py_func)) {
                symbols.push_back({"function", match[1], lineno});
            } else if (std::regex_search(line, match, py_class)) {
                symbols.push_back({"class", match[1], lineno});
            }
        } else if (lang == "cpp" || lang == "c") {
            if (std::regex_search(line, match, cpp_func)) {
                symbols.push_back({"function", match[1], lineno});
            } else if (std::regex_search(line, match, cpp_class)) {
                symbols.push_back({"class", match[1], lineno});
            }
        }
    }
    return symbols;
}

int code_context_cli(int argc, char** argv) {
    if (argc < 2) {
        std::cout << "Usage: " << argv[0] << " <file_or_directory>\n";
        return 1;
    }
    std::string path = argv[1];
    CodeParser parser;

    if (std::filesystem::is_directory(path)) {
        for (const auto& entry : std::filesystem::recursive_directory_iterator(path)) {
            if (!entry.is_regular_file()) continue;
            std::string file = entry.path().string();
            std::string lang = parser.detect_language(file);
            if (lang == "unknown") continue;
            auto symbols = parser.scan_file(file);
            if (!symbols.empty()) {
                std::cout << "File: " << file << " (" << lang << ")\n";
                for (const auto& sym : symbols) {
                    std::cout << "  " << sym.type << " " << sym.name << " at line " << sym.line << "\n";
                }
            }
        }
    } else {
        std::string lang = parser.detect_language(path);
        auto symbols = parser.scan_file(path);
        std::cout << "File: " << path << " (" << lang << ")\n";
        for (const auto& sym : symbols) {
            std::cout << "  " << sym.type << " " << sym.name << " at line " << sym.line << "\n";
        }
    }
    return 0;
}

} // namespace code
} // namespace voicelink
