// FinLift – lift of the caudal fin (quasi-static flat-plate model).
//
// Why: for ordinary bodies Stonefish 1.5 computes buoyancy, added mass and drag on every
// mesh face, but the force on a face acts ALONG the relative water velocity (pure drag).
// A fin moving sideways therefore only gets a sideways force – with no forward component.
// The library does not compute lift (perpendicular to the inflow), yet that is what gives fish their thrust.
// (Diagnosis and numbers: README, "Thrust diagnosis".)
//
// Model (blade-element, a single plate at the middle of the fin):
//   u   – fin velocity relative to the water, projected onto the fin's XY plane (chord X, normal Y),
//   α   – angle of attack between the chord and the inflow, reduced to [0°, 90°],
//   C_L = ½·C_Lα·sin(2α)   (≈ C_Lα·α for small angles, maximum at 45°, 0 at 90°;
//                           shape as in measurements of flapping plates: Dickinson et al., Science 1999),
//   L   = ½·ρ·S·C_L·|u|²,  direction perpendicular to u, opposite to the fin motion along the normal axis.
// Fin drag stays as Stonefish computes it from the mesh – we do not add it a second time.
//
// Works as a link actuator (LinkActuator): Stonefish calls Update() at the start of
// every step, after the forces are cleared, just like for the built-in "rudder".
#pragma once

#include <Stonefish/actuators/LinkActuator.h>

namespace fish
{
    // Lift in the fin frame for relative velocity (ux, uy) [m/s].
    // Returns (Lx, Ly) [N]. Pure function – tested in tests/unit_tests.cpp.
    void FinLiftForce(double ux, double uy, double rho, double area, double clAlpha, double& Lx, double& Ly);

    class FinLift : public sf::LinkActuator
    {
    public:
        FinLift(const std::string& name, double area, double clAlpha);
        void Update(sf::Scalar dt) override;
        sf::ActuatorType getType() const override { return sf::ActuatorType::RUDDER; }
        double lastLift() const { return lift_; }       // |L| [N] – for the log
        double lastAlphaDeg() const { return alphaDeg_; }
        double lastThrust() const { return thrust_; }   // component of L along the head X axis [N] (computed by the manager)
        void setThrust(double t) { thrust_ = t; }
        sf::Vector3 lastForceWorld() const { return Fw_; }

    private:
        double area_, clAlpha_;
        double lift_ = 0.0, alphaDeg_ = 0.0, thrust_ = 0.0;
        sf::Vector3 Fw_;
    };
}
