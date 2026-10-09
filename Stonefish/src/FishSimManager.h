// FishSimManager – the heart of the demo: loads the XML scenario, in every physics step
// computes the hydraulics and control, applies the torques, drives the VBS and writes the CSV log.
// The same class works in the graphical and the console application.
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
    // Current state – for the overlay in the graphical app and for console printouts.
    // A force in the head frame: fwd = along the head X axis (+ = forward), side = along Y (+ = right).
    struct ForceFS { double fwd = 0, side = 0; };

    struct FishStatus
    {
        double t = 0, speed = 0, depth = 0, depthMeas = 0, depthRef = 0;
        double freq = 0, biasMl = 0, pL = 0, pR = 0, vbsMl = 0, yawDeg = 0;
        bool rhythmOn = false, depthOn = false, headingOn = false;
        // drive: torque from the hydraulics [N·m], pump command u, pump flow Q [m³/s], joint angles [deg]
        double tailTorque = 0, u = 0, Q = 0;
        std::vector<double> thetaDeg;
        // water forces [N]: drag (pressure + skin friction) per part, fin lift (our FinLift), total
        ForceFS dragHead, dragTail, dragFin, finLift, water;
        double finAlphaDeg = 0;
    };

    class FishSimManager : public sf::SimulationManager
    {
    public:
        explicit FishSimManager(const Config& cfg);
        ~FishSimManager() override;

        void BuildScenario() override;
        void SimulationStepCompleted(sf::Scalar timeStep) override;

        // CSV log (empty path = no log). The file is opened at the first step.
        void SetLogPath(const std::string& path) { logPath_ = path; }
        // Called when the simulation time exceeds duration (the console app exits).
        void SetOnFinished(std::function<void()> cb, double duration) { onFinished_ = std::move(cb); duration_ = duration; }

        // Keyboard control (graphical app) – changes on the fly.
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
        // True center of mass, linear momentum and angular momentum (Z axis) of the whole fish – for the internal actuation test.
        void ComputeMomentum(sf::Vector3& com, sf::Vector3& P, double& Lz) const;

        Config cfg_;
        bool parsedOk_ = false;
        std::string massReport_;
        std::string stiffnessReport_;
        std::string frictionReport_;

        // robot parts (the pointers are owned by Stonefish)
        sf::FeatherstoneRobot* robot_ = nullptr;
        std::vector<sf::SolidEntity*> links_;      // [Head, Seg1..SegN, Fin] – the tail chain
        std::vector<sf::SolidEntity*> allLinks_;   // links_ + bodies welded to the head (Dorsal)
        std::vector<sf::Motor*> motors_;
        std::vector<sf::RotaryEncoder*> encoders_;
        sf::VariableBuoyancy* vbs_ = nullptr;
        sf::Pressure* pressure_ = nullptr;
        sf::IMU* imu_ = nullptr;
        FinLift* finLift_ = nullptr;   // nullptr when fin_lift.enabled = false

        // models and controllers
        std::unique_ptr<TailHydraulics> hyd_;
        std::unique_ptr<TailDriver> driver_;
        std::unique_ptr<TailRhythm> rhythm_;
        std::unique_ptr<DepthController> depthCtrl_;
        std::unique_ptr<HeadingController> headingCtrl_;
        bool rhythmOn_ = false, depthOn_ = false, headingOn_ = false, locked_ = false;
        std::vector<std::pair<double, double>> depthSchedule_;
        double rhoG_ = 9810.0;
        double yawRef_ = 0.0;
        int depthEvery_ = 10;          // depth controller runs every this many steps (= sensor rate)

        // state in the current step (for the log)
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
