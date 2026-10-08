// Wspólne argumenty linii poleceń obu aplikacji:
//   <plik.json>               – konfiguracja scenariusza (np. config/s2_swim.json)
//   --out <plik.csv>          – log CSV (domyślnie: results/logs/<nazwa scenariusza>.csv w konsoli, brak w GUI)
//   --set sekcja.klucz=wart   – nadpisanie parametru (można wiele razy)
//   --duration <s>            – skrót do --set sim.duration=<s>
//   --window <szer>x<wys>     – rozmiar okna GUI w pikselach (domyślnie 90% ekranu)
#pragma once

#include <cstdio>
#include <cstdlib>
#include <filesystem>
#include <iostream>
#include <string>
#include <vector>

namespace fish
{
    struct AppArgs
    {
        std::string rootDir;
        std::string configFile;
        std::string outFile;
        std::vector<std::string> overrides;
        int windowW = 0, windowH = 0;   // 0 = automatycznie

        static void Usage(const char* prog)
        {
            std::cerr << "Użycie: " << prog << " config/<scenariusz>.json [--out plik.csv] [--set sekcja.klucz=wartość]... [--duration s] [--window SZERxWYS]\n";
        }

        static AppArgs Parse(int argc, char** argv)
        {
            AppArgs a;
            // Katalog projektu: zmienna FISH_ROOT albo katalog źródeł zapisany przy kompilacji.
            const char* env = std::getenv("FISH_ROOT");
            a.rootDir = env ? env : FISH_ROOT_DIR;
            for(int i = 1; i < argc; ++i)
            {
                std::string s = argv[i];
                auto next = [&]() -> std::string {
                    if(i + 1 >= argc) { Usage(argv[0]); std::exit(2); }
                    return argv[++i];
                };
                if(s == "--out") a.outFile = next();
                else if(s == "--set") a.overrides.push_back(next());
                else if(s == "--duration") a.overrides.push_back("sim.duration=" + next());
                else if(s == "--window")
                {
                    const std::string v = next();
                    if(std::sscanf(v.c_str(), "%dx%d", &a.windowW, &a.windowH) != 2 || a.windowW < 320 || a.windowH < 240)
                    { std::cerr << "--window wymaga postaci SZERxWYS, np. 1600x900\n"; std::exit(2); }
                }
                else if(s == "-h" || s == "--help") { Usage(argv[0]); std::exit(0); }
                else if(a.configFile.empty()) a.configFile = s;
                else { Usage(argv[0]); std::exit(2); }
            }
            if(a.configFile.empty()) { Usage(argv[0]); std::exit(2); }
            // ścieżka względna: najpierw względem bieżącego katalogu, potem katalogu projektu
            if(!std::filesystem::exists(a.configFile) && std::filesystem::exists(a.rootDir + "/" + a.configFile))
                a.configFile = a.rootDir + "/" + a.configFile;
            return a;
        }
    };
}
