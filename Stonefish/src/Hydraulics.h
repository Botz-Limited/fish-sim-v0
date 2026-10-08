// Hydraulika ogona: pompa + dwie komory (L, R) w układzie zamkniętym.
// Ten sam model co w demo MuJoCo (../MuJoCo/fishsim/hydraulics.py), przepisany 1:1 do C++,
// żeby wyniki obu symulatorów dało się porównać.
//
// Stany:
//   Q        – przepływ pompy z R do L [m³/s] (człon inercyjny I rzędu, stała τ_pump),
//   V_L, V_R – objętości cieczy w komorach [m³]; V_L + V_R = const (układ zamknięty).
//
// "Sprężyna hydrauliczna": pompa przetłoczyła V_p = (V_L − V_R)/2, a ogon zgięty o
// L = Σ w_i·θ_i "zrobił miejsce" na A_eff·r_eff·L. Nadmiar ściska ciecz i rozpycha
// podatne ścianki (podatność C_h):
//   Δp = p_L − p_R = (V_p − A_eff·r_eff·L) / C_h,   ograniczone zaworem do ±p_max,
//   moment na "tendonie" F = A_eff·r_eff·Δp  [N·m] (rozkładany na przeguby wagami w_i).
//
// Całkowanie: jawny Euler z krokiem fizyki. Moment liczony ze stanu NA POCZĄTKU kroku.
// Stabilne, bo dt ≪ τ_pump i ω_n·dt ≪ 2 dla sprężyny hydraulicznej (README).
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
        double Q_max;       // [m³/s]
        double tau_pump;    // [s]
    };

    class TailHydraulics
    {
    public:
        explicit TailHydraulics(const HydraulicsParams& p);

        // Jeden krok: komenda pompy u ∈ [−1, 1], aktualna "długość tendonu" L [rad].
        // Zwraca moment F [N·m] do przyłożenia w TYM kroku (ze stanu przed aktualizacją).
        double Step(double u, double L, double dt);

        double DeltaP(double L) const;   // p_L − p_R [Pa]
        double ForceOnTendon(double L) const { return Ar_ * DeltaP(L); }
        double pL(double L) const { return 0.5 * DeltaP(L); }   // względem ciśnienia wstępnego
        double pR(double L) const { return -0.5 * DeltaP(L); }
        double Vp() const { return 0.5 * (VL_ - VR_); }

        double Q() const { return Q_; }
        double VL() const { return VL_; }
        double VR() const { return VR_; }
        double Qvalve() const { return Qvalve_; }
        double Ar() const { return Ar_; }
        // Sztywność sprężyny hydraulicznej widziana przez tendon k_h = (A_eff·r_eff)²/C_h.
        double StiffnessHydraulic() const { return Ar_ * Ar_ / p_.C_h; }
        const HydraulicsParams& params() const { return p_; }

    private:
        HydraulicsParams p_;
        double Ar_;      // A_eff·r_eff [m³/rad] – objętość "zajęta" przez ogon na radian L
        double Q_;
        double VL_, VR_;
        double Qvalve_;  // przepływ przez zawór przelewowy [m³/s], >0 = z L do R
    };
}
