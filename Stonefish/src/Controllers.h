// Control: tail rhythm (CPG), turning, depth controller (VBS), heading controller.
// The classes do not depend on Stonefish – they take measurements and return commands.
#pragma once

#include <utility>
#include <vector>

namespace fish
{
    // ------------------------------------------------------------------ tail CPG
    // The generator commands the pumped VOLUME, not the flow:
    //   V_ref(t) = a(t)·A_V·sin(2πft + φ0) + V_bias
    // Why not a flow command proportional to sin(2πft) + bias (as in SPEC): the volume in a chamber
    // is the INTEGRAL of the flow, so a constant bias would integrate without bound until the relief
    // valve locks the tail on one side. Here the bias is a volume -> constant tail deflection -> turning.
    // a(t) – soft start ½(1 − cos(πt/T)) over ramp_time seconds.
    //
    // The pump runs at constant speed, so the only command is the valve state s = ±1.
    // Hysteresis relay (state s remembered between steps, s = +1 at start / reset):
    //   e = V_ref − V_p;   e > δ -> s = +1;   e < −δ -> s = −1;   otherwise s unchanged.
    // While 2πf·A_V < Q_const, V_p follows V_ref as a "saw" (band ≈ ±δ plus an overshoot
    // ≈ Q_const·τ_valve, many valve switches per cycle). Above f_track = Q_const/(2π·A_V) the valve
    // switches only at the peaks (2 per cycle), V_p is a triangle with amplitude ≈ Q_const/(4f) (scenario 6).
    //
    // Hardware limits: the valve switches at most ~5 times/s, so each state is held for at least
    // minDwell (valve_min_dwell = 0.2 s) – the relay ignores the error until then. The frequency is
    // clamped to [fMin, fMax]: below f_track the "saw" regime would need fast chattering the valve
    // cannot do; above 1/(2·minDwell) the valve cannot make 2 switches per cycle.
    class TailRhythm
    {
    public:
        TailRhythm(double freq, double amp, double bias, double hysteresis, double rampTime,
                   double minDwell, double fMin, double fMax);
        std::pair<double, double> Vref(double t) const;   // (V_ref, dV_ref/dt)
        int Command(double t, double Vp);                 // valve state s ∈ {−1, +1} (updates the relay)
        int valve() const { return s_; }
        long switches() const { return switches_; }   // valve switches (sign changes of s) since start
        // Frequency change without a phase jump (φ chosen so that the phase is continuous).
        // f is clamped to [fMin, fMax] (also in the constructor).
        void SetFreq(double f, double t);
        double Clamp(double f) const;
        double freq() const { return f_; }
        double bias = 0.0;     // [m³] V_bias – can be changed on the fly (turning, heading controller)
        double amp = 0.0;      // [m³] A_V

    private:
        double delta_, ramp_, minDwell_, fMin_, fMax_, f_;
        double phase0_ = 0.0;
        int s_ = +1;           // relay state; a new TailRhythm (simulation reset) starts with s = +1
        double tSwitch_ = -1e300;   // [s] time of the last valve switch (−∞ at start / reset)
        long switches_ = 0;
    };

    // ------------------------------------------------------------------ first-order filter
    // y += (x − y)·dt/(τ + dt), τ = 1/(2π·f_c). Passes slow changes (the true
    // depth), attenuates fast sensor noise. The price: a delay of ~τ (here 0.16 s at 1 Hz).
    class LowPass
    {
    public:
        explicit LowPass(double cutoffHz) : tau_(cutoffHz > 0 ? 1.0 / (2.0 * 3.14159265358979 * cutoffHz) : 0.0) {}
        double Update(double x, double dt);
        double value() const { return y_; }
        void Reset(double y) { y_ = y; init_ = true; }

    private:
        double tau_;
        double y_ = 0.0;
        bool init_ = false;
    };

    // ------------------------------------------------------------------ depth
    // Cascade: depth PID -> REFERENCE water volume in the VBS V_ref -> ballast pump.
    // NED: d = depth (+ down). More water in the VBS = more weight = the fish sinks.
    //   e    = d_f − d_ref           (> 0: fish too deep)
    //   V_ref = V_n − Kp·e − Kd·ḋ_f − Ki·∫e
    // d_f, ḋ_f – depth and rate from the FILTERED pressure sensor measurement.
    // The D term acts on the rate (not on the error), so a step in d_ref gives no "kick".
    // Anti-windup (two mechanisms):
    //  1) the integral grows only when the output is not saturated in the direction of the error,
    //  2) conditional integration: only when |e| < iBand. Without it, on a 2 m step the integral
    //     accumulates ∫e over the whole slow transit (the output need not be saturated at all)
    //     and causes a large overshoot (scenario 4, README).
    struct DepthParams
    {
        double kp, ki, kd;
        double iBand;             // [m] integrate only close to the target
        double lpfCutoffHz;
        double zMin;              // [m] shallowest allowed reference depth
        double Vmin, Vmax, Vn;    // VBS range and neutral volume [m³]
    };

    class DepthController
    {
    public:
        explicit DepthController(const DepthParams& p);
        // depthMeasured – from the pressure sensor [m], dt – controller period [s]. Returns V_ref [m³].
        double Update(double depthMeasured, double dt);
        void SetReference(double dRef);
        double reference() const { return dRef_; }
        double depthFiltered() const { return lpfDepth_.value(); }
        double rateFiltered() const { return lpfRate_.value(); }
        double integral() const { return integral_; }

    private:
        DepthParams p_;
        double dRef_ = 1.0;
        double integral_ = 0.0;
        LowPass lpfDepth_, lpfRate_;
        double prevDepth_ = 0.0;
        bool init_ = false;
    };

    // Ballast pump: tracks V_ref with limited flow rate, Q = clip(k·(V_ref − V), ±q_max).
    double VbsFlowCommand(double Vref, double V, double kTrack, double qMax);

    // ------------------------------------------------------------------ heading (scenario 5)
    // PI on the IMU yaw -> tail V_bias. Sign (verified in scenario 3): V_bias > 0
    // bends the tail to the LEFT (−Y in NED) and the fish turns left (yaw decreases). When the fish has drifted left
    // (yaw < yaw_ref, error e = yaw_ref − yaw > 0), it must turn right -> bias < 0:
    //   V_bias = −(K_p·e + K_i·∫e)
    class HeadingController
    {
    public:
        HeadingController(double kp, double ki, double biasMax);
        double Update(double yawMeasured, double yawRef, double dt);   // returns V_bias [m³]

    private:
        double kp_, ki_, biasMax_;
        double integral_ = 0.0;
    };

    // Angle wrapped to (−π, π].
    double WrapAngle(double a);
}
