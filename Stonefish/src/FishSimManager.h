// FishSimManager – serce demo: ładuje scenariusz XML, w każdym kroku fizyki
// liczy hydraulikę i sterowanie, przykłada momenty, steruje VBS i zapisuje log CSV.
// Ta sama klasa działa w aplikacji graficznej i konsolowej.
#pragma once

#include <Stonefish/core/SimulationManager.h>

#include <array>
#include <fstream>
#include <functional>
#include <memory>
#include <string>
#include <vector>

#include "Config.h"
#include "Controllers.h"
#include "FinLift.h"
#include "Hydraulics.h"
#include "TailDriver.h"

namespace sf
{
    class FeatherstoneRobot;
    class Motor;
    class VariableBuoyancy;
    class Pressure;
    class IMU;
    class RotaryEncoder;
    class SolidEntity;
}

namespace fish
{
    // Stan "na teraz" – do nakładki w aplikacji graficznej i do wydruków w konsoli.
    struct FishStatus
    {
        double t = 0, speed = 0, depth = 0, depthMeas = 0, depthRef = 0;
        double freq = 0, biasMl = 0, pL = 0, pR = 0, vbsMl = 0, yawDeg = 0;
        bool rhythmOn = false, depthOn = false, headingOn = false;
    };

    class FishSimManager : public sf::SimulationManager
    {
    public:
        explicit FishSimManager(const Config& cfg);
        ~FishSimManager() override;

        void BuildScenario() override;
        void SimulationStepCompleted(sf::Scalar timeStep) override;

        // Log CSV (pusta ścieżka = bez logu). Plik otwierany przy pierwszym kroku.
        void SetLogPath(const std::string& path) { logPath_ = path; }
        // Wywoływane, gdy czas symulacji przekroczy duration (aplikacja konsolowa kończy pracę).
        void SetOnFinished(std::function<void()> cb, double duration) { onFinished_ = std::move(cb); duration_ = duration; }

        // Sterowanie z klawiatury (aplikacja graficzna) – zmiany w locie.
        void ToggleRhythm();
        void ChangeFreq(double df);
        void ChangeBias(double dV);
        void ChangeDepthRef(double dz);

        FishStatus Status() const;
        bool ParsedOk() const { return parsedOk_; }
        std::string MassReport() const { return massReport_; }
        sf::SolidEntity* Head() const { return links_.empty() ? nullptr : links_[0]; }
        const Config& config() const { return cfg_; }

    private:
        void FindRobotParts();
        void BuildMassReport();
        void ResetControl();
        std::vector<double> JointStiffness();
        void ApplySkinFriction();
        void WriteLogHeader();
        void WriteLogRow();
        // Prawdziwy środek masy, pęd i moment pędu (oś Z) całej ryby – do testu napędu wewnętrznego.
        void ComputeMomentum(sf::Vector3& com, sf::Vector3& P, double& Lz) const;

        Config cfg_;
        bool parsedOk_ = false;
        std::string massReport_;
        std::string stiffnessReport_;
        std::string frictionReport_;

        // elementy robota (wskaźniki należą do Stonefish)
        sf::FeatherstoneRobot* robot_ = nullptr;
        std::vector<sf::SolidEntity*> links_;      // [Head, Seg1..SegN, Fin] – łańcuch ogona
        std::vector<sf::SolidEntity*> allLinks_;   // links_ + bryły przyspawane do głowy (Dorsal)
        std::vector<sf::Motor*> motors_;
        std::vector<sf::RotaryEncoder*> encoders_;
        sf::VariableBuoyancy* vbs_ = nullptr;
        sf::Pressure* pressure_ = nullptr;
        sf::IMU* imu_ = nullptr;
        FinLift* finLift_ = nullptr;   // nullptr, gdy fin_lift.enabled = false

        // modele i regulatory
        std::unique_ptr<TailHydraulics> hyd_;
        std::unique_ptr<TailDriver> driver_;
        std::unique_ptr<TailRhythm> rhythm_;
        std::unique_ptr<DepthController> depthCtrl_;
        std::unique_ptr<HeadingController> headingCtrl_;
        bool rhythmOn_ = false, depthOn_ = false, headingOn_ = false, locked_ = false;
        std::vector<std::pair<double, double>> depthSchedule_;
        double rhoG_ = 9810.0;
        double yawRef_ = 0.0;
        int depthEvery_ = 10;          // regulator głębokości co tyle kroków (= częstotliwość czujnika)

        // stan w bieżącym kroku (do logu)
        long step_ = 0;
        double u_ = 0, F_ = 0, L_ = 0;
        std::vector<double> theta_, omega_, tau_;
        double depthMeas_ = 0, vbsRef_ = 0, vbsFlow_ = 0, tauSum_ = 0;

        // log
        std::string logPath_;
        std::ofstream log_;
        int logEvery_ = 5;
        std::function<void()> onFinished_;
        double duration_ = 1e30;
        bool finished_ = false;
    };
}
