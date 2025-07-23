#pragma once

#include <string>
#include <vector>

namespace voicelink {
namespace code {

struct CodeSymbol {
    std::string type;
    std::string name;
    int line;
};

class CodeParser {
public:
    std::vector<CodeSymbol> scan_file(const std::string& file_path);
    std::string detect_language(const std::string& file_path);
};

// CLI function
int code_context_cli(int argc, char** argv);

} // namespace code
} // namespace voicelink
