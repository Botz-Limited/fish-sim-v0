#include "Config.h"

#include <fstream>
#include <stdexcept>

namespace fish
{
    json LoadJsonFile(const std::string& path)
    {
        std::ifstream f(path);
        if(!f)
            throw std::runtime_error("Nie mogę otworzyć pliku konfiguracji: " + path);
        // parse(wejście, callback, wyjątki, ignore_comments=true) – komentarze // są dozwolone
        return json::parse(f, nullptr, true, true);
    }

    Config Config::Load(const std::string& rootDir, const std::string& scenarioFile,
                        const std::vector<std::string>& overrides)
    {
        Config c;
        c.rootDir = rootDir;
        c.sourceFile = scenarioFile;
        c.j = LoadJsonFile(rootDir + "/config/default.json");
        if(!scenarioFile.empty())
            c.j.merge_patch(LoadJsonFile(scenarioFile));

        for(const std::string& ov : overrides)
        {
            // "sekcja.klucz=wartość" -> {"sekcja": {"klucz": wartość}}
            size_t eq = ov.find('=');
            if(eq == std::string::npos)
                throw std::runtime_error("--set wymaga postaci sekcja.klucz=wartość, jest: " + ov);
            std::string path = ov.substr(0, eq);
            std::string val = ov.substr(eq + 1);
            json v;
            try { v = json::parse(val); }
            catch(const json::parse_error&) { v = val; } // nie-JSON -> napis (np. nazwa pliku)

            json patch = v;
            size_t end = path.size();
            while(true)
            {
                size_t dot = path.rfind('.', end - 1);
                std::string key = path.substr(dot == std::string::npos ? 0 : dot + 1,
                                              end - (dot == std::string::npos ? 0 : dot + 1));
                patch = json{{key, patch}};
                if(dot == std::string::npos) break;
                end = dot;
            }
            c.j.merge_patch(patch);
        }
        return c;
    }

    const json& Config::at(const std::string& section) const
    {
        if(!j.contains(section))
            throw std::runtime_error("Brak sekcji konfiguracji: " + section);
        return j.at(section);
    }

    double Config::d(const std::string& section, const std::string& key) const
    {
        const json& s = at(section);
        if(!s.contains(key))
            throw std::runtime_error("Brak parametru: " + section + "." + key);
        return s.at(key).get<double>();
    }

    bool Config::b(const std::string& section, const std::string& key) const
    {
        const json& s = at(section);
        if(!s.contains(key))
            throw std::runtime_error("Brak parametru: " + section + "." + key);
        return s.at(key).get<bool>();
    }

    std::string Config::s(const std::string& section, const std::string& key) const
    {
        const json& s = at(section);
        if(!s.contains(key))
            throw std::runtime_error("Brak parametru: " + section + "." + key);
        return s.at(key).get<std::string>();
    }
}
