// Wczytywanie parametrów z config/*.json (JSON z komentarzami //).
//
// Kolejność (każdy następny nadpisuje poprzedni, scalanie RFC 7396 "merge-patch"):
//   1. config/default.json            – wszystkie parametry z opisem,
//   2. plik scenariusza, np. config/s2_swim.json – tylko to, co inne,
//   3. --set sekcja.klucz=wartość     – pojedyncze pola z linii poleceń
//      (wartość jako JSON: liczba, true/false, tablica; inaczej traktowana jako napis).
// Dzięki temu parametry zmienia się bez rekompilacji.
#pragma once

#include <nlohmann/json.hpp>
#include <string>
#include <vector>

namespace fish
{
    using json = nlohmann::json;

    struct Config
    {
        json j;                 // scalona konfiguracja
        std::string rootDir;    // katalog Stonefish/ (z config/, data/, results/)
        std::string sourceFile; // plik scenariusza (do logów)

        // Wczytuje default.json + scenarioFile + nadpisania "a.b=wartość".
        static Config Load(const std::string& rootDir, const std::string& scenarioFile,
                           const std::vector<std::string>& overrides);

        // Skróty: cfg.d("hydraulics", "C_h") itp. Brak pola = wyjątek z czytelnym komunikatem.
        double d(const std::string& section, const std::string& key) const;
        bool b(const std::string& section, const std::string& key) const;
        std::string s(const std::string& section, const std::string& key) const;
        const json& at(const std::string& section) const;
    };

    // Odczyt pliku JSON z komentarzami.
    json LoadJsonFile(const std::string& path);
}
