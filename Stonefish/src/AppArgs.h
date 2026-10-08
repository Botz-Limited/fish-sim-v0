// Command-line arguments shared by both applications:
//   <file.json>               – scenario configuration (e.g. config/s2_swim.json)
//   --out <file.csv>          – CSV log (default: results/logs/<scenario name>.csv in the console app, none in the GUI)
//   --set section.key=value   – parameter override (can be repeated)
//   --duration <s>            – shortcut for --set sim.duration=<s>
//   --window <width>x<height> – GUI window size in pixels (default 90% of the screen)
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
        int windowW = 0, windowH = 0;   // 0 = automatic

        static void Usage(const char* prog)
        {
            std::cerr << "Usage: " << prog << " config/<scenario>.json [--out file.csv] [--set section.key=value]... [--duration s] [--window WxH]\n";
        }

        static AppArgs Parse(int argc, char** argv)
        {
            AppArgs a;
            // Project directory: the FISH_ROOT variable or the source directory recorded at compile time.
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
                    { std::cerr << "--window requires the form WxH, e.g. 1600x900\n"; std::exit(2); }
                }
                else if(s == "-h" || s == "--help") { Usage(argv[0]); std::exit(0); }
                else if(a.configFile.empty()) a.configFile = s;
                else { Usage(argv[0]); std::exit(2); }
            }
            if(a.configFile.empty()) { Usage(argv[0]); std::exit(2); }
            // relative path: first relative to the current directory, then to the project directory
            if(!std::filesystem::exists(a.configFile) && std::filesystem::exists(a.rootDir + "/" + a.configFile))
                a.configFile = a.rootDir + "/" + a.configFile;
            return a;
        }
    };
}
