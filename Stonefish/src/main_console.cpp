// Aplikacja KONSOLOWA: bez okna i bez renderingu (sf::ConsoleSimulationApp).
// Symulacja ze stałym krokiem, tak szybko, jak pozwala procesor (nie w czasie rzeczywistym),
// przez sim.duration sekund; wynik w pliku CSV. Do testów i scenariuszy wsadowych.
// Ograniczenia trybu konsolowego (dokumentacja Stonefish): brak kamer, świateł i fal.

#include <Stonefish/core/ConsoleSimulationApp.h>

#include <chrono>
#include <filesystem>
#include <iostream>

#include "AppArgs.h"
#include "FishSimManager.h"

namespace
{
    // Quit() jest w bibliotece "protected" – udostępniamy go, żeby zakończyć po zadanym czasie.
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
    catch(const std::exception& e) { std::cerr << "BŁĄD konfiguracji: " << e.what() << "\n"; return 2; }

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
        // Run(autostart, autostep, krok): krok > 0 -> stały krok, bez czekania na zegar.
        app.Run(true, true, 1.0 / sps);
    }
    catch(const std::exception& e)
    {
        std::cerr << "BŁĄD: " << e.what() << "\n";
        return 1;
    }
    if(!manager->ParsedOk())
    {
        std::cerr << "BŁĄD: scenariusz nie wczytał się poprawnie (komunikaty parsera powyżej).\n";
        return 1;
    }
    const double wall = std::chrono::duration<double>(std::chrono::steady_clock::now() - t0).count();
    std::cout << "Zakończono: " << duration << " s symulacji w " << wall << " s (x" << duration / wall
              << " czasu rzeczywistego). Log: " << args.outFile << "\n";
    return 0;
}
