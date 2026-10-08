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
        // Ciśnienie ze ZNAKIEM: dodatnie = komora L ma wyższe ciśnienie.
        return (Vp() - Ar_ * L) / p_.C_h;
    }

    double TailHydraulics::Step(double u, double L, double dt)
    {
        const double F = ForceOnTendon(L);   // jawnie: siła ze stanu na początku kroku
        u = std::clamp(u, -1.0, 1.0);

        // Pompa rozpędza się do u·Q_max ze stałą czasową τ_pump (człon I rzędu).
        Q_ += dt * (u * p_.Q_max - Q_) / p_.tau_pump;

        // Pompa przetacza ciecz z R do L – suma objętości się nie zmienia.
        VL_ += Q_ * dt;
        VR_ -= Q_ * dt;

        // Zawór przelewowy łączy komory: gdy |Δp| przekroczyłoby p_max, przepuszcza
        // nadmiar z komory o wyższym ciśnieniu do drugiej (też bez zmiany sumy).
        const double excess = Vp() - Ar_ * L;
        const double limit = p_.p_max * p_.C_h;               // nadmiar objętości odpowiadający p_max
        const double vent = excess - std::clamp(excess, -limit, limit);
        // Vp = (V_L − V_R)/2, więc przesunięcie "vent" z L do R zmienia Vp dokładnie o −vent.
        VL_ -= vent;
        VR_ += vent;
        Qvalve_ = vent / dt;
        return F;
    }
}
