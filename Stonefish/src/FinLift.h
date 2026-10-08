// FinLift – siła nośna płetwy ogonowej (quasi-statyczny model płaskiej płytki).
//
// Po co: Stonefish 1.5 liczy dla zwykłych brył wypór, masę dołączoną i opór na każdej
// ściance siatki, ale siła na ściankę działa WZDŁUŻ prędkości względnej wody (czysty opór).
// Płetwa poruszająca się na boki dostaje więc siłę tylko na boki – bez składowej do przodu.
// Siły nośnej (prostopadłej do napływu) biblioteka nie liczy, a to ona daje ciąg ryb.
// (Diagnoza i liczby: README, "Diagnoza ciągu".)
//
// Model (blade-element, jedna płytka w środku płetwy):
//   u   – prędkość płetwy względem wody, rzut na płaszczyznę XY płetwy (cięciwa X, normalna Y),
//   α   – kąt natarcia między cięciwą a napływem, sprowadzony do [0°, 90°],
//   C_L = ½·C_Lα·sin(2α)   (≈ C_Lα·α dla małych kątów, maksimum przy 45°, 0 przy 90°;
//                           kształt jak w pomiarach płytek machających: Dickinson i in., Science 1999),
//   L   = ½·ρ·S·C_L·|u|²,  kierunek prostopadły do u, przeciwny do ruchu płetwy w osi normalnej.
// Opór płetwy zostaje taki, jak liczy go Stonefish z siatki – nie dodajemy go drugi raz.
//
// Działa jako aktuator ogniwa (LinkActuator): Stonefish wywołuje Update() na początku
// każdego kroku, po wyzerowaniu sił, tak jak dla wbudowanego "rudder".
#pragma once

#include <Stonefish/actuators/LinkActuator.h>

namespace fish
{
    // Siła nośna w układzie płetwy dla prędkości względnej (ux, uy) [m/s].
    // Zwraca (Lx, Ly) [N]. Funkcja czysta – testowana w tests/unit_tests.cpp.
    void FinLiftForce(double ux, double uy, double rho, double area, double clAlpha, double& Lx, double& Ly);

    class FinLift : public sf::LinkActuator
    {
    public:
        FinLift(const std::string& name, double area, double clAlpha);
        void Update(sf::Scalar dt) override;
        sf::ActuatorType getType() const override { return sf::ActuatorType::RUDDER; }
        double lastLift() const { return lift_; }       // |L| [N] – do logu
        double lastAlphaDeg() const { return alphaDeg_; }
        double lastThrust() const { return thrust_; }   // składowa L wzdłuż osi X głowy [N] (liczy manager)
        void setThrust(double t) { thrust_ = t; }
        sf::Vector3 lastForceWorld() const { return Fw_; }

    private:
        double area_, clAlpha_;
        double lift_ = 0.0, alphaDeg_ = 0.0, thrust_ = 0.0;
        sf::Vector3 Fw_;
    };
}
