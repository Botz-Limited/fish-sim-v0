// Tail hydraulics: constant-speed pump + directional valves + two chambers (L, R) in a closed circuit.
// The same model as in the MuJoCo demo (../MuJoCo/fishsim/hydraulics.py), ported 1:1 to C++,
// so that the results of both simulators can be compared.
//
// States:
//   Q        – flow from R to L [m³/s]. The pump runs at CONSTANT speed and delivers Q_const;
//              the directional valves only choose the direction: s = +1 (R→L) or s = −1 (L→R).
//              There is no "closed" valve state; s = 0 means only "pump off" (no rhythm).
//              Switching the valves and reversing the stream takes time: first-order lag
//              dQ/dt = (s·Q_const − Q)/τ_valve,
//   V_L, V_R – fluid volumes in the chambers [m³]; V_L + V_R = const (closed circuit).
//
// "Hydraulic spring": the pump has transferred V_p = (V_L − V_R)/2, and the tail bent by
// L = Σ w_i·θ_i has "made room" for A_eff·r_eff·L. The excess compresses the fluid and pushes
// the compliant walls outward (compliance C_h):
//   Δp = p_L − p_R = (V_p − A_eff·r_eff·L) / C_h,   limited by the valve to ±p_max,
//   torque on the "tendon" F = A_eff·r_eff·Δp  [N·m] (distributed over the joints with weights w_i).
//
// Integration: explicit Euler with the physics step. Torque computed from the state AT THE START of the step.
// Stable because dt ≪ τ_valve and ω_n·dt ≪ 2 for the hydraulic spring (README).
#pragma once

namespace fish
{
    struct HydraulicsParams
    {
        double A_eff;       // [m²]
        double r_eff;       // [m]
        double C_h;         // [m³/Pa]
        double p_max;       // [Pa]
        double V0_chamber;  // [m³]
        double Q_const;     // [m³/s] constant pump delivery
        double tau_valve;   // [s] valve switching + flow reversal time
    };

    class TailHydraulics
    {
    public:
        explicit TailHydraulics(const HydraulicsParams& p);

        // One step: valve state s ∈ {−1, +1} (0 = pump off), current "tendon length" L [rad].
        // Returns the torque F [N·m] to apply in THIS step (from the state before the update).
        double Step(int s, double L, double dt);

        double DeltaP(double L) const;   // p_L − p_R [Pa]
        double ForceOnTendon(double L) const { return Ar_ * DeltaP(L); }
        double pL(double L) const { return 0.5 * DeltaP(L); }   // relative to the pre-charge pressure
        double pR(double L) const { return -0.5 * DeltaP(L); }
        double Vp() const { return 0.5 * (VL_ - VR_); }

        double Q() const { return Q_; }
        double VL() const { return VL_; }
        double VR() const { return VR_; }
        double Qvalve() const { return Qvalve_; }
        double Ar() const { return Ar_; }
        // Stiffness of the hydraulic spring as seen by the tendon k_h = (A_eff·r_eff)²/C_h.
        double StiffnessHydraulic() const { return Ar_ * Ar_ / p_.C_h; }
        const HydraulicsParams& params() const { return p_; }

    private:
        HydraulicsParams p_;
        double Ar_;      // A_eff·r_eff [m³/rad] – volume "taken up" by the tail per radian of L
        double Q_;
        double VL_, VR_;
        double Qvalve_;  // flow through the relief valve [m³/s], >0 = from L to R
    };
}
