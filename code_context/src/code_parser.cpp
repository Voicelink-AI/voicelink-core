#include "code_parser.h"
#include <fstream>
#include <regex>
#include <iostream>
#include <filesystem>

namespace voicelink {
namespace code {

std::string CodeParser::detect_language(const std::string& file_path) {
    std::filesystem::path path(file_path);
    std::string extension = path.extension().string();
    
    if (extension == ".py") return "python";
    if (extension == ".cpp" || extension == ".cc" || extension == ".cxx") return "cpp";
    if (extension == ".c") return "c";
    if (extension == ".h" || extension == ".hpp") return "header";
    if (extension == ".js") return "javascript";
    if (extension == ".ts") return "typescript";
    if (extension == ".java") return "java";
    if (extension == ".go") return "go";
    if (extension == ".rs") return "rust";
    
    return "unknown";
}

std::vector<CodeSymbol> CodeParser::scan_file(const std::string& file_path) {
    std::vector<CodeSymbol> symbols;
    
    std::ifstream file(file_path);
    if (!file.is_open()) {
        std::cerr << "Cannot open file: " << file_path << std::endl;
        return symbols;
    }
    
    std::string language = detect_language(file_path);
    std::string line;
    int line_number = 0;
    
    // Language-specific patterns
    std::vector<std::regex> patterns;
    if (language == "python") {
        patterns = {
            std::regex(R"(^def\s+(\w+)\s*\()"),           // Functions
            std::regex(R"(^class\s+(\w+)\s*[:(\(])"),     // Classes
            std::regex(R"(^(\w+)\s*=)"),                  // Variables
            std::regex(R"(import\s+(\w+))"),              // Imports
            std::regex(R"(from\s+(\w+)\s+import)"),       // From imports
        };
    } else if (language == "cpp" || language == "c") {
        patterns = {
            std::regex(R"(^\s*(\w+)\s+(\w+)\s*\([^)]*\)\s*\{)"), // Functions
            std::regex(R"(^\s*class\s+(\w+))"),                  // Classes
            std::regex(R"(^\s*struct\s+(\w+))"),                 // Structs
            std::regex(R"(#include\s*[<"]([^>"]+)[>"])"),        // Includes
        };
    } else if (language == "javascript" || language == "typescript") {
        patterns = {
            std::regex(R"(function\s+(\w+)\s*\()"),       // Functions
            std::regex(R"(const\s+(\w+)\s*=)"),          // Constants
            std::regex(R"(class\s+(\w+))"),              // Classes
            std::regex(R"(import.*from\s+['"]([^'"]+)['"])"), // Imports
        };
    }
    
    while (std::getline(file, line)) {
        line_number++;
        
        for (const auto& pattern : patterns) {
            std::smatch match;
            if (std::regex_search(line, match, pattern)) {
                CodeSymbol symbol;
                symbol.name = match[1].str();
                symbol.line = line_number;
                
                // Determine symbol type based on pattern
                if (line.find("def ") != std::string::npos || 
                    line.find("function ") != std::string::npos) {
                    symbol.type = "function";
                } else if (line.find("class ") != std::string::npos) {
                    symbol.type = "class";
                } else if (line.find("import") != std::string::npos || 
                           line.find("#include") != std::string::npos) {
                    symbol.type = "import";
                } else {
                    symbol.type = "variable";
                }
                
                symbols.push_back(symbol);
                break;
            }
        }
    }
    
    return symbols;
}

#ifdef BUILD_CLI
int code_context_cli(int argc, char** argv) {
    if (argc < 2) {
        std::cout << "Usage: " << argv[0] << " <file_or_directory>\n";
        return 1;
    }
    
    std::string path = argv[1];
    CodeParser parser;
    
    if (std::filesystem::is_directory(path)) {
        std::cout << "Scanning directory: " << path << std::endl;
        
        for (const auto& entry : std::filesystem::recursive_directory_iterator(path)) {
            if (entry.is_regular_file()) {
                std::string file_path = entry.path().string();
                std::string language = parser.detect_language(file_path);
                
                if (language != "unknown") {
                    auto symbols = parser.scan_file(file_path);
                    
                    if (!symbols.empty()) {
                        std::cout << "\nFile: " << file_path << " (" << language << ")\n";
                        for (const auto& symbol : symbols) {
                            std::cout << "  " << symbol.type << ": " << symbol.name 
                                     << " (line " << symbol.line << ")\n";
                        }
                    }
                }
            }
        }
    } else {
        auto symbols = parser.scan_file(path);
        std::cout << "File: " << path << std::endl;
        for (const auto& symbol : symbols) {
            std::cout << symbol.type << ": " << symbol.name 
                     << " (line " << symbol.line << ")\n";
        }
    }
    
    return 0;
}

// Main function for CLI
int main(int argc, char** argv) {
    return code_context_cli(argc, argv);
}
#endif

} // namespace code
} // namespace voicelink
