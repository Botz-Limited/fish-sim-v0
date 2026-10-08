#include "Controllers.h"

#include <algorithm>
#include <cmath>

namespace fish
{
    // ------------------------------------------------------------------ TailRhythm

    TailRhythm::TailRhythm(double freq, double amp_, double bias_, double Kv, double Qmax, double rampTime)
        : bias(bias_), amp(amp_), f_(freq), Kv_(Kv), Qmax_(Qmax), ramp_(rampTime)
    {
    }

    std::pair<double, double> TailRhythm::Vref(double t) const
    {
        // miękki start a(t) i jego pochodna
        double a = 1.0, da = 0.0;
        if(ramp_ > 0.0 && t < ramp_)
        {
            a = 0.5 * (1.0 - std::cos(M_PI * t / ramp_));
            da = 0.5 * M_PI / ramp_ * std::sin(M_PI * t / ramp_);
        }
        const double w = 2.0 * M_PI * f_;
        const double s = std::sin(w * t + phase0_);
        const double c = std::cos(w * t + phase0_);
        return {a * amp * s + bias, amp * (da * s + a * w * c)};
    }

    double TailRhythm::Command(double t, double Vp) const
    {
        auto [v, dv] = Vref(t);
        // feed-forward (przepływ, który "powinien" płynąć) + korekta błędu objętości
        const double u = (dv + Kv_ * (v - Vp)) / Qmax_;
        return std::clamp(u, -1.0, 1.0);
    }

    void TailRhythm::SetFreq(double f, double t)
    {
        // faza φ(t) = 2πf·t + φ0 ma być ciągła w chwili t
        phase0_ += 2.0 * M_PI * (f_ - f) * t;
        f_ = f;
    }

    // ------------------------------------------------------------------ LowPass

    double LowPass::Update(double x, double dt)
    {
        if(!init_)
        {
            y_ = x;
            init_ = true;
            return y_;
        }
        y_ += (x - y_) * dt / (tau_ + dt);
        return y_;
    }

    // ------------------------------------------------------------------ DepthController

    DepthController::DepthController(const DepthParams& p)
        : p_(p), lpfDepth_(p.lpfCutoffHz), lpfRate_(p.lpfCutoffHz)
    {
    }

    void DepthController::SetReference(double dRef)
    {
        dRef_ = std::max(dRef, p_.zMin);   // regulator nie wyciąga ryby na powierzchnię
    }

    double DepthController::Update(double depthMeasured, double dt)
    {
        // 1) filtr dolnoprzepustowy na zaszumionym pomiarze
        const double d = lpfDepth_.Update(depthMeasured, dt);
        // 2) prędkość z różnicy filtrowanej głębokości, jeszcze raz filtrowana
        //    (różniczkowanie wzmacnia szum: σ_v ≈ √2·σ_d/dt)
        if(!init_)
        {
            prevDepth_ = d;
            lpfRate_.Reset(0.0);
            init_ = true;
        }
        const double rate = lpfRate_.Update((d - prevDepth_) / dt, dt);
        prevDepth_ = d;

        const double e = d - dRef_;     // > 0: za głęboko -> mniej wody
        const double vPD = p_.Vn - p_.kp * e - p_.kd * rate;
        double vOut = vPD - p_.ki * integral_;
        const bool satHi = vOut >= p_.Vmax;   // pełny zbiornik (najciężej)
        const bool satLo = vOut <= p_.Vmin;   // pusty (najlżej)
        // anti-windup: nie całkujemy, gdy całka pchałaby wyjście dalej w nasycenie
        if(std::fabs(e) < p_.iBand && !((satLo && e > 0) || (satHi && e < 0)))
        {
            integral_ += e * dt;
            // całka sama nie może przesunąć wyjścia o więcej niż pół zakresu VBS
            const double iMax = 0.5 * (p_.Vmax - p_.Vmin) / std::max(p_.ki, 1e-30);
            integral_ = std::clamp(integral_, -iMax, iMax);
        }
        vOut = vPD - p_.ki * integral_;
        return std::clamp(vOut, p_.Vmin, p_.Vmax);
    }

    double VbsFlowCommand(double Vref, double V, double kTrack, double qMax)
    {
        return std::clamp(kTrack * (Vref - V), -qMax, qMax);
    }

    // ------------------------------------------------------------------ HeadingController

    double WrapAngle(double a)
    {
        a = std::fmod(a + M_PI, 2.0 * M_PI);
        if(a <= 0.0) a += 2.0 * M_PI;
        return a - M_PI;
    }

    HeadingController::HeadingController(double kp, double ki, double biasMax)
        : kp_(kp), ki_(ki), biasMax_(biasMax)
    {
    }

    double HeadingController::Update(double yawMeasured, double yawRef, double dt)
    {
        const double e = WrapAngle(yawRef - yawMeasured);
        const double out = kp_ * e + ki_ * integral_;      // "ile skrętu w prawo" [m³]
        // anti-windup: całkujemy tylko poza nasyceniem (albo gdy uchyb z niego wyprowadza)
        if(std::fabs(out) < biasMax_ || out * e < 0.0)
            integral_ += e * dt;
        return -std::clamp(kp_ * e + ki_ * integral_, -biasMax_, biasMax_);
    }
}
