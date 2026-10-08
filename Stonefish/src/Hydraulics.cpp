#include "Hydraulics.h"

#include <algorithm>

namespace fish
{
    TailHydraulics::TailHydraulics(const HydraulicsParams& p)
        : p_(p), Ar_(p.A_eff * p.r_eff), Q_(0.0), VL_(p.V0_chamber), VR_(p.V0_chamber), Qvalve_(0.0)
    {
    }

    double TailHydraulics::DeltaP(double L) const
    {
        // SIGNED pressure: positive = chamber L has the higher pressure.
        return (Vp() - Ar_ * L) / p_.C_h;
    }

    double TailHydraulics::Step(double u, double L, double dt)
    {
        const double F = ForceOnTendon(L);   // explicit: force from the state at the start of the step
        u = std::clamp(u, -1.0, 1.0);

        // The pump spins up to u·Q_max with time constant τ_pump (first-order lag).
        Q_ += dt * (u * p_.Q_max - Q_) / p_.tau_pump;

        // The pump moves fluid from R to L – the total volume does not change.
        VL_ += Q_ * dt;
        VR_ -= Q_ * dt;

        // The relief valve connects the chambers: when |Δp| would exceed p_max, it passes
        // the excess from the higher-pressure chamber to the other (also without changing the total).
        const double excess = Vp() - Ar_ * L;
        const double limit = p_.p_max * p_.C_h;               // excess volume corresponding to p_max
        const double vent = excess - std::clamp(excess, -limit, limit);
        // Vp = (V_L − V_R)/2, so moving "vent" from L to R changes Vp by exactly −vent.
        VL_ -= vent;
        VR_ += vent;
        Qvalve_ = vent / dt;
        return F;
    }
}
