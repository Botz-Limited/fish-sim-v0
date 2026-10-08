// Sterowanie: rytm ogona (CPG), skręt, regulator głębokości (VBS), regulator kursu.
// Klasy nie zależą od Stonefish – dostają pomiary, zwracają komendy.
#pragma once

#include <utility>
#include <vector>

namespace fish
{
    // ------------------------------------------------------------------ CPG ogona
    // Generator zadaje OBJĘTOŚĆ przepompowaną, nie przepływ:
    //   V_ref(t) = a(t)·A_V·sin(2πft + φ0) + V_bias
    //   u = clip((dV_ref/dt + K_v·(V_ref − V_p)) / Q_max, −1, 1)
    // Dlaczego nie u = A·sin(2πft) + bias (jak w SPEC): objętość w komorze to CAŁKA
    // z przepływu, więc stały bias w u całkowałby się bez końca, aż zawór przelewowy
    // zablokuje ogon po jednej stronie. Sam sinus też daje przesunięcie: ∫sin = 1 − cos ≥ 0.
    // Tu bias jest objętością -> stałe ugięcie ogona -> skręt.
    // a(t) – miękki start ½(1 − cos(πt/T)) przez ramp_time sekund.
    // Gdy 2πf·A_V > Q_max, pompa się nasyca (|u| = 1) i amplituda spada (scenariusz 6).
    class TailRhythm
    {
    public:
        TailRhythm(double freq, double amp, double bias, double Kv, double Qmax, double rampTime);
        std::pair<double, double> Vref(double t) const;   // (V_ref, dV_ref/dt)
        double Command(double t, double Vp) const;        // u ∈ [−1, 1]
        // Zmiana częstotliwości bez skoku fazy (φ dobierane tak, żeby faza była ciągła).
        void SetFreq(double f, double t);
        double freq() const { return f_; }
        double bias = 0.0;     // [m³] V_bias – można zmieniać w trakcie (skręt, regulator kursu)
        double amp = 0.0;      // [m³] A_V

    private:
        double f_, Kv_, Qmax_, ramp_;
        double phase0_ = 0.0;
    };

    // ------------------------------------------------------------------ filtr I rzędu
    // y += (x − y)·dt/(τ + dt), τ = 1/(2π·f_c). Przepuszcza wolne zmiany (prawdziwa
    // głębokość), tłumi szybki szum czujnika. Cena: opóźnienie ~τ (tu 0.16 s przy 1 Hz).
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

    // ------------------------------------------------------------------ głębokość
    // Kaskada: PID głębokości -> ZADANA objętość wody w VBS V_ref -> pompa balastowa.
    // NED: d = głębokość (+ w dół). Więcej wody w VBS = większy ciężar = ryba opada.
    //   e    = d_f − d_ref           (> 0: ryba za głęboko)
    //   V_ref = V_n − Kp·e − Kd·ḋ_f − Ki·∫e
    // d_f, ḋ_f – głębokość i prędkość z FILTROWANEGO pomiaru czujnika ciśnienia.
    // Człon D działa na prędkość (nie na uchyb), więc skok d_ref nie daje "kopnięcia".
    // Anti-windup (dwa mechanizmy):
    //  1) całka rośnie tylko, gdy wyjście nie jest nasycone w kierunku uchybu,
    //  2) całkowanie warunkowe: tylko gdy |e| < iBand. Bez tego przy skoku o 2 m całka
    //     zbiera ∫e przez cały, wolny przejazd (wyjście wcale nie musi być nasycone)
    //     i daje duże przeregulowanie (scenariusz 4, README).
    struct DepthParams
    {
        double kp, ki, kd;
        double iBand;             // [m] całkujemy tylko blisko celu
        double lpfCutoffHz;
        double zMin;              // [m] najpłytsza dozwolona głębokość zadana
        double Vmin, Vmax, Vn;    // zakres VBS i objętość neutralna [m³]
    };

    class DepthController
    {
    public:
        explicit DepthController(const DepthParams& p);
        // depthMeasured – z czujnika ciśnienia [m], dt – okres regulatora [s]. Zwraca V_ref [m³].
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

    // Pompa balastowa: śledzi V_ref z ograniczonym wydatkiem, Q = clip(k·(V_ref − V), ±q_max).
    double VbsFlowCommand(double Vref, double V, double kTrack, double qMax);

    // ------------------------------------------------------------------ kurs (scenariusz 5)
    // PI na odchyleniu z IMU -> V_bias ogona. Znak (sprawdzony w scenariuszu 3): V_bias > 0
    // zgina ogon w LEWO (−Y w NED) i ryba skręca w lewo (yaw maleje). Gdy ryba zboczyła w lewo
    // (yaw < yaw_ref, uchyb e = yaw_ref − yaw > 0), trzeba skręcić w prawo -> bias < 0:
    //   V_bias = −(K_p·e + K_i·∫e)
    class HeadingController
    {
    public:
        HeadingController(double kp, double ki, double biasMax);
        double Update(double yawMeasured, double yawRef, double dt);   // zwraca V_bias [m³]

    private:
        double kp_, ki_, biasMax_;
        double integral_ = 0.0;
    };

    // Kąt sprowadzony do (−π, π].
    double WrapAngle(double a);
}
