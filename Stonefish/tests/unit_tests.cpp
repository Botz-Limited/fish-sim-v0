// Unit tests of the models independent of Stonefish (no window, no rigid-body physics).
//   - hydraulics: V_L + V_R = const, |p_L − p_R| ≤ p_max, pressure sign,
//   - TailDriver: sum of drive torques on all bodies = 0 (internal actuation),
//   - controllers: filter, anti-windup, angle wrapping.
// Run: build/unit_tests (returns exit code 1 if any test fails).

#include <cmath>
#include <cstdio>
#include <random>
#include <string>
#include <vector>

#include "Config.h"
#include "Controllers.h"
#include "FinLift.h"
#include "Hydraulics.h"
#include "TailDriver.h"

namespace
{
    int failures = 0;

    void check(bool ok, const std::string& what)
    {
        std::printf("  [%s] %s\n", ok ? " OK " : "FAIL", what.c_str());
        if(!ok) ++failures;
    }

    fish::HydraulicsParams params(const fish::Config& c)
    {
        const auto& h = c.at("hydraulics");
        return {h.at("A_eff"), h.at("r_eff"), h.at("C_h"), h.at("p_max"), h.at("V0_chamber"), h.at("Q_max"), h.at("tau_pump")};
    }
}

int main()
{
    using namespace fish;
    const Config cfg = Config::Load(FISH_ROOT_DIR, "", {});
    const HydraulicsParams hp = params(cfg);
    const double dt = 1.0 / cfg.d("sim", "steps_per_second");

    // ------------------------------------------------------------------ hydraulics
    std::printf("Hydraulics:\n");
    {
        // The pump runs randomly, the tail is held (L = 0) or flapping – we check the invariants.
        TailHydraulics hyd(hp);
        std::mt19937 rng(1);
        std::uniform_real_distribution<double> U(-1.0, 1.0);
        const double Vsum0 = hyd.VL() + hyd.VR();
        double maxSumErr = 0.0, maxDp = 0.0;
        for(int i = 0; i < 20000; ++i)
        {
            const double t = i * dt;
            const double L = (i < 10000) ? 0.0 : 0.3 * std::sin(2 * M_PI * 2.0 * t);
            hyd.Step(U(rng) > -0.2 ? 1.0 : -1.0, L, dt);   // "+" dominates: the pump pushes one way
            maxSumErr = std::max(maxSumErr, std::fabs(hyd.VL() + hyd.VR() - Vsum0));
            maxDp = std::max(maxDp, std::fabs(hyd.DeltaP(L)));
        }
        check(maxSumErr < 1e-15, "V_L + V_R = const (max error " + std::to_string(maxSumErr) + " m³)");
        check(maxDp <= hp.p_max * (1 + 1e-9), "|p_L − p_R| ≤ p_max (max " + std::to_string(maxDp) + " Pa)");
        check(maxDp > 0.99 * hp.p_max, "relief valve actually opened (Δp reached p_max)");
    }
    {
        // Pump stopped and the tail bent by L > 0: chamber L "expanded" -> underpressure, Δp < 0,
        // torque F < 0 tries to straighten the tail (hydraulic spring).
        TailHydraulics hyd(hp);
        const double L = 0.01;
        check(hyd.DeltaP(L) < 0 && hyd.ForceOnTendon(L) < 0, "tail bent with the pump stopped -> restoring torque");
        check(std::fabs(hyd.StiffnessHydraulic() - 5.0) < 1e-9, "k_h = (A_eff·r_eff)²/C_h = 5 N·m/rad (as in MuJoCo)");
    }
    {
        // Pump at full flow: after ~5τ the flow = Q_max (first-order lag).
        TailHydraulics hyd(hp);
        for(int i = 0; i < (int)(5 * hp.tau_pump / dt); ++i) hyd.Step(1.0, 1e3, dt);  // large L: the valve does not open
        check(std::fabs(hyd.Q() - hp.Q_max) < 0.01 * hp.Q_max, "first-order pump: Q -> Q_max after 5·τ_pump");
    }

    // ------------------------------------------------------------------ TailDriver
    std::printf("TailDriver:\n");
    {
        TailDriver drv(5, 3, 0.4, {0.3, 0.3, 0.3, 1.287, 0.528});
        const auto& w = drv.weights();
        check(std::fabs(w[0] - 1.0) < 1e-12 && std::fabs(w[1] - 0.7) < 1e-12 && std::fabs(w[2] - 0.4) < 1e-12
              && w[3] == 0.0 && w[4] == 0.0, "tendon weights 1, 0.7, 0.4, 0, 0");
        std::mt19937 rng(2);
        std::uniform_real_distribution<double> U(-1.0, 1.0);
        double maxSum = 0.0;
        for(int k = 0; k < 1000; ++k)
        {
            std::vector<double> th(5);
            for(double& x : th) x = 0.6 * U(rng);
            const auto tau = drv.JointTorques(0.5 * U(rng), th);
            double s = 0.0;
            for(double x : TailDriver::LinkTorques(tau)) s += x;
            maxSum = std::max(maxSum, std::fabs(s));
        }
        check(maxSum < 1e-15, "sum of drive torques on the whole robot = 0 (internal actuation)");
        const auto tau = drv.JointTorques(1.0, {0.1, 0, 0, 0.1, 0});
        check(std::fabs(tau[0] - (1.0 - 0.03)) < 1e-12 && std::fabs(tau[3] + 0.1287) < 1e-12,
              "τ_i = w_i·F − k_i·θ_i");
        const auto zero = drv.JointTorques(1.0, {0.1, 0, 0, 0, 0}, true);
        check(zero[0] == 0.0, "tail locked -> torques 0");
    }

    // ------------------------------------------------------------------ fin lift
    std::printf("FinLift:\n");
    {
        double Lx, Ly;
        const double rho = 1000, S = 0.0066, cla = 2.8;
        // The fish swims forward (fin relative to water: ux > 0), the fin moves in +Y:
        // the lift has a −Y component (resists the sideways motion) and +X (THRUST) – likewise for motion in −Y.
        FinLiftForce(0.3, 0.3, rho, S, cla, Lx, Ly);
        check(Lx > 0 && Ly < 0, "fin in +Y while moving forward: thrust (+X) and a force resisting sideways motion (−Y)");
        double Lx2, Ly2;
        FinLiftForce(0.3, -0.3, rho, S, cla, Lx2, Ly2);
        check(Lx2 > 0 && Ly2 > 0 && std::fabs(Lx2 - Lx) < 1e-12, "fin in −Y: same thrust, sideways force in +Y");
        FinLiftForce(0.0, 0.5, rho, S, cla, Lx, Ly);
        check(std::fabs(Lx) < 1e-12 && std::fabs(Ly) < 1e-12, "plate broadside to the flow (α = 90°): no lift");
        FinLiftForce(0.5, 0.0, rho, S, cla, Lx, Ly);
        check(std::fabs(Lx) < 1e-12 && std::fabs(Ly) < 1e-12, "α = 0: no lift");
        FinLiftForce(0.5, 0.5, rho, S, cla, Lx, Ly);
        const double expected = 0.5 * rho * S * (0.5 * cla) * 0.5;   // α = 45°: C_L = ½·C_Lα, u² = 0.5
        check(std::fabs(std::hypot(Lx, Ly) - expected) < 1e-12 && std::fabs(Lx * 0.5 + Ly * 0.5) < 1e-12,
              "α = 45°: |L| = ½ρS·½C_Lα·u², L perpendicular to u");
    }

    // ------------------------------------------------------------------ controllers
    std::printf("Controllers:\n");
    {
        // First-order filter: noise σ = 5 mm at constant depth -> after the filter σ is clearly smaller.
        LowPass lp(1.0);
        std::mt19937 rng(3);
        std::normal_distribution<double> N(0.0, 0.005);
        double s2raw = 0, s2f = 0;
        const double dts = 0.02;
        for(int i = 0; i < 5000; ++i)
        {
            const double n = N(rng);
            const double y = lp.Update(2.0 + n, dts);
            if(i > 100) { s2raw += n * n; s2f += (y - 2.0) * (y - 2.0); }
        }
        const double ratio = std::sqrt(s2f / s2raw);
        check(ratio < 0.4, "1 Hz filter attenuates sensor noise (σ_after/σ_before = " + std::to_string(ratio) + ")");
    }
    {
        // Depth controller: fish 1 m too deep -> V_ref at the lower limit (empty tank),
        // and the integral does not grow (anti-windup).
        DepthParams p{24e-6, 0.7e-6, 160e-6, 0.2, 1.0, 0.3, 0.5e-6, 40.5e-6, 20.5e-6};
        DepthController dc(p);
        dc.SetReference(1.0);
        double v = 0;
        for(int i = 0; i < 500; ++i) v = dc.Update(2.0, 0.02);
        check(std::fabs(v - p.Vmin) < 1e-15, "too deep -> VBS emptied (V_ref = V_min)");
        check(std::fabs(dc.integral()) < 1e-9, "anti-windup: integral does not grow in saturation");
        dc.SetReference(0.1);
        check(std::fabs(dc.reference() - 0.3) < 1e-12, "reference depth limited to z_min");
        check(std::fabs(VbsFlowCommand(40e-6, 0.0, 5.0, 10e-6) - 10e-6) < 1e-18, "VBS pump limited to q_max");
    }
    {
        check(std::fabs(WrapAngle(3 * M_PI / 2) + M_PI / 2) < 1e-12 && std::fabs(WrapAngle(-3 * M_PI / 2) - M_PI / 2) < 1e-12,
              "angle wrapping to (−π, π]");
        TailRhythm r(2.0, 8e-6, 0.0, 10.0, 60e-6, 1.0);
        const double v1 = r.Vref(3.1).first;
        r.SetFreq(1.0, 3.1);
        check(std::fabs(r.Vref(3.1).first - v1) < 1e-15, "CPG frequency change without a phase jump");
    }

    std::printf(failures ? "\n%d test(s) FAILED.\n" : "\nAll unit tests passed.\n", failures);
    return failures ? 1 : 0;
}
