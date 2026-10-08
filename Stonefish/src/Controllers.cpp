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
        // soft start a(t) and its derivative
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
        // feed-forward (the flow that "should" be flowing) + volume error correction
        const double u = (dv + Kv_ * (v - Vp)) / Qmax_;
        return std::clamp(u, -1.0, 1.0);
    }

    void TailRhythm::SetFreq(double f, double t)
    {
        // the phase φ(t) = 2πf·t + φ0 must be continuous at time t
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
        dRef_ = std::max(dRef, p_.zMin);   // the controller does not pull the fish up to the surface
    }

    double DepthController::Update(double depthMeasured, double dt)
    {
        // 1) low-pass filter on the noisy measurement
        const double d = lpfDepth_.Update(depthMeasured, dt);
        // 2) rate from the difference of the filtered depth, filtered once more
        //    (differentiation amplifies noise: σ_v ≈ √2·σ_d/dt)
        if(!init_)
        {
            prevDepth_ = d;
            lpfRate_.Reset(0.0);
            init_ = true;
        }
        const double rate = lpfRate_.Update((d - prevDepth_) / dt, dt);
        prevDepth_ = d;

        const double e = d - dRef_;     // > 0: too deep -> less water
        const double vPD = p_.Vn - p_.kp * e - p_.kd * rate;
        double vOut = vPD - p_.ki * integral_;
        const bool satHi = vOut >= p_.Vmax;   // full tank (heaviest)
        const bool satLo = vOut <= p_.Vmin;   // empty (lightest)
        // anti-windup: do not integrate when the integral would push the output further into saturation
        if(std::fabs(e) < p_.iBand && !((satLo && e > 0) || (satHi && e < 0)))
        {
            integral_ += e * dt;
            // the integral alone may not shift the output by more than half the VBS range
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
        const double out = kp_ * e + ki_ * integral_;      // "how much right turn" [m³]
        // anti-windup: integrate only outside saturation (or when the error drives out of it)
        if(std::fabs(out) < biasMax_ || out * e < 0.0)
            integral_ += e * dt;
        return -std::clamp(kp_ * e + ki_ * integral_, -biasMax_, biasMax_);
    }
}
