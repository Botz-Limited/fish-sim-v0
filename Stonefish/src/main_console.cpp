// CONSOLE application: no window and no rendering (sf::ConsoleSimulationApp).
// Fixed-step simulation, as fast as the CPU allows (not in real time),
// for sim.duration seconds; the result goes to a CSV file. For tests and batch scenarios.
// Console mode limitations (Stonefish documentation): no cameras, lights or waves.

#include <Stonefish/core/ConsoleSimulationApp.h>

#include <chrono>
#include <filesystem>
#include <iostream>

#include "AppArgs.h"
#include "FishSimManager.h"

namespace
{
    // Quit() is "protected" in the library – we expose it to finish after the given time.
    class FishConsoleApp : public sf::ConsoleSimulationApp
    {
    public:
        using sf::ConsoleSimulationApp::ConsoleSimulationApp;
        void Finish() { Quit(); }
    };
}

int main(int argc, char** argv)
{
    using namespace fish;
    AppArgs args = AppArgs::Parse(argc, argv);
    Config cfg;
    try { cfg = Config::Load(args.rootDir, args.configFile, args.overrides); }
    catch(const std::exception& e) { std::cerr << "ERROR (config): " << e.what() << "\n"; return 2; }

    if(args.outFile.empty())
    {
        const std::string stem = std::filesystem::path(args.configFile).stem().string();
        std::filesystem::create_directories(args.rootDir + "/results/logs");
        args.outFile = args.rootDir + "/results/logs/" + stem + ".csv";
    }

    const double sps = cfg.d("sim", "steps_per_second");
    const double duration = cfg.d("sim", "duration");
    FishSimManager mgr(cfg);
    FishSimManager* manager = &mgr;
    manager->SetLogPath(args.outFile);
    FishConsoleApp app("Fish Stonefish (console)", args.rootDir + "/data/", manager);
    manager->SetOnFinished([&app]() { app.Finish(); }, duration);

    const auto t0 = std::chrono::steady_clock::now();
    try
    {
        // Run(autostart, autostep, step): step > 0 -> fixed step, without waiting for the clock.
        app.Run(true, true, 1.0 / sps);
    }
    catch(const std::exception& e)
    {
        std::cerr << "ERROR: " << e.what() << "\n";
        return 1;
    }
    if(!manager->ParsedOk())
    {
        std::cerr << "ERROR: the scenario did not load correctly (parser messages above).\n";
        return 1;
    }
    const double wall = std::chrono::duration<double>(std::chrono::steady_clock::now() - t0).count();
    std::cout << "Finished: " << duration << " s of simulation in " << wall << " s (x" << duration / wall
              << " real time). Log: " << args.outFile << "\n";
    return 0;
}
