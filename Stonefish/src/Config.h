// Loading parameters from config/*.json (JSON with // comments).
//
// Order (each one overrides the previous, merged per RFC 7396 "merge-patch"):
//   1. config/default.json            – all parameters with descriptions,
//   2. scenario file, e.g. config/s2_swim.json – only what differs,
//   3. --set section.key=value        – individual fields from the command line
//      (value as JSON: number, true/false, array; otherwise treated as a string).
// This way parameters can be changed without recompiling.
#pragma once

#include <nlohmann/json.hpp>
#include <string>
#include <vector>

namespace fish
{
    using json = nlohmann::json;

    struct Config
    {
        json j;                 // merged configuration
        std::string rootDir;    // the Stonefish/ directory (with config/, data/, results/)
        std::string sourceFile; // scenario file (for logs)

        // Loads default.json + scenarioFile + "a.b=value" overrides.
        static Config Load(const std::string& rootDir, const std::string& scenarioFile,
                           const std::vector<std::string>& overrides);

        // Shortcuts: cfg.d("hydraulics", "C_h") etc. Missing field = exception with a readable message.
        double d(const std::string& section, const std::string& key) const;
        bool b(const std::string& section, const std::string& key) const;
        std::string s(const std::string& section, const std::string& key) const;
        const json& at(const std::string& section) const;
    };

    // Reads a JSON file with comments.
    json LoadJsonFile(const std::string& path);
}
