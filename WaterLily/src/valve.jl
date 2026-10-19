# Valve and hydraulics: constant-speed pump + ±1 directional valve.
# Port of MuJoCo `fishsim` and OpenFOAM `tools/make_actuation.py` (same model):
#
#   V_ref(t) = r(t)·A_V·sin(2πft) + V_bias          r = ramp 0 -> 1 over t_ramp (default 1 period)
#   relay:   e = V_ref − V_p;  e > δ -> s = +1;  e < −δ -> s = −1  (else s unchanged; start s = +1)
#            ignored until t − t_switch ≥ min_dwell (the first switch is free)
#   dQ/dt   = (s·Q_const − Q)/tau_valve      exact exponential step
#   dV_p/dt = Q                              trapezoid
#
# The ODE is integrated on a FIXED internal grid t_k = k·dt (dt = DT_VALVE), as
# in make_actuation.py; the relay is evaluated at the grid nodes and the dwell
# is counted in whole steps (no round-off). A streaming `Valve` can be advanced
# to any time inside a CFD loop; between nodes the state is evaluated with a
# partial exact/trapezoid step, so V_p(t) is continuous and smooth enough for
# the body velocity. `valve_series` uses the same stepper, so both give
# bit-identical node values.

"""
    check_freq(f; p=VALVE)

Return `f` if it lies in the valve's frequency range `[p.f_min, p.f_max]`
(1.5–2.5 Hz), otherwise throw an `ArgumentError`. No silent clamping.
"""
function check_freq(f; p::ValveParams=VALVE)
    if !(p.f_min - 1e-9 <= f <= p.f_max + 1e-9)
        throw(ArgumentError(
            "tail frequency $(f) Hz is outside the valve range [$(p.f_min), $(p.f_max)] Hz " *
            "(min. dwell $(p.min_dwell) s -> at most 2 switches per cycle up to " *
            "$(1/(2p.min_dwell)) Hz; below ≈ f_track = Q_const/(2π A_V) the relay would chatter)"))
    end
    return f
end

"f_track = Q_const/(2π A_V): below it the relay would track V_ref with a sawtooth."
f_track(p::ValveParams=VALVE) = p.Q_const / (2π * p.A_V)

"""
    Valve(f; p=VALVE, t_ramp=1/f, dt=DT_VALVE, check=true)

Streaming valve model at tail frequency `f` [Hz]. Advance with
`advance!(v, t)` and read with `valve_state(v, t)`. Time is physical [s].
"""
mutable struct Valve
    p::ValveParams
    f::Float64
    t_ramp::Float64
    dt::Float64
    a::Float64        # exp(-dt/tau_valve)
    n_dwell::Int      # min dwell in whole steps
    k::Int            # current node index, t_k = k·dt
    V::Float64        # V_p at node k [m^3]
    Q::Float64        # Q at node k [m^3/s]
    s::Float64        # valve state chosen at node k (held over [t_k, t_k+dt))
    k_switch::Int     # node of the last switch
    n_switch::Int     # total number of switches
end

function Valve(f; p::ValveParams=VALVE, t_ramp=1/f, dt=DT_VALVE, check=true)
    check && check_freq(f; p)
    n_dwell = ceil(Int, p.min_dwell / dt - 1e-9)
    v = Valve(p, Float64(f), Float64(t_ramp), Float64(dt), exp(-dt / p.tau_valve),
              n_dwell, 0, 0.0, 0.0, 1.0, -n_dwell, 0)
    _relay!(v)          # decision at node 0
    return v
end

ramp(t, t_ramp) = t_ramp > 0 ? clamp(t / t_ramp, 0.0, 1.0) : 1.0

"Volume reference V_ref(t) [m^3]."
vref(v::Valve, t) = ramp(t, v.t_ramp) * v.p.A_V * sin(2π * v.f * t) + v.p.V_bias

function _relay!(v::Valve)
    v.k - v.k_switch >= v.n_dwell || return v
    e = vref(v, v.k * v.dt) - v.V
    s_new = e > v.p.delta ? 1.0 : (e < -v.p.delta ? -1.0 : v.s)
    if s_new != v.s
        v.s = s_new; v.k_switch = v.k; v.n_switch += 1
    end
    return v
end

# one fixed step node k -> k+1, then the relay decision at node k+1
function _step!(v::Valve)
    sq = v.s * v.p.Q_const
    q_new = sq + (v.Q - sq) * v.a
    v.V += 0.5 * (v.Q + q_new) * v.dt
    v.Q = q_new
    v.k += 1
    _relay!(v)
end

"Physical time of the current node."
node_time(v::Valve) = v.k * v.dt

"""
    advance!(v::Valve, t)

Integrate the valve up to physical time `t` (the last node ≤ t). Never goes back.
"""
function advance!(v::Valve, t)
    while (v.k + 1) * v.dt <= t + 1e-12
        _step!(v)
    end
    return v
end

"""
    valve_state(v::Valve, t) -> (; t, V_ref, V_p, Q, s)

State at physical time `t` (advances the valve if needed). Between nodes a
partial exact (Q) / trapezoid (V_p) step from the last node is used.
"""
function valve_state(v::Valve, t)
    advance!(v, t)
    τ = max(t - node_time(v), 0.0)
    sq = v.s * v.p.Q_const
    q = sq + (v.Q - sq) * exp(-τ / v.p.tau_valve)
    V = v.V + 0.5 * (v.Q + q) * τ
    return (; t=Float64(t), V_ref=vref(v, t), V_p=V, Q=q, s=v.s)
end

"Kinematic mode: chamber volume becomes bending one-to-one, θ = V_p/A_r [rad]."
theta_kinematic(V_p, p::ValveParams=VALVE) = V_p / p.A_r

"Chamber pressure difference Δp = clip((V_p − A_r·θ)/C_h, ±p_max) [Pa] (coupled mode)."
chamber_dp(V_p, θ, p::ValveParams=VALVE) = clamp((V_p - p.A_r * θ) / p.C_h, -p.p_max, p.p_max)

"""
    valve_series(f, t_end; p=VALVE, t_ramp=1/f, dt=DT_VALVE, check=true)
        -> (; t, V_ref, V_p, Q, s)

Whole series on the node grid 0:dt:t_end (same stepper as `Valve`).
"""
function valve_series(f, t_end; p::ValveParams=VALVE, t_ramp=1/f, dt=DT_VALVE, check=true)
    v = Valve(f; p, t_ramp, dt, check)
    n = ceil(Int, t_end / dt - 1e-9) + 1
    t = zeros(n); Vr = zeros(n); V = zeros(n); Q = zeros(n); s = zeros(n)
    for k in 1:n
        k > 1 && _step!(v)
        t[k] = node_time(v); Vr[k] = vref(v, t[k]); V[k] = v.V; Q[k] = v.Q; s[k] = v.s
    end
    return (; t, V_ref=Vr, V_p=V, Q, s)
end

"""
    switch_times(t, s)

Times at which the valve state changes (first sample after the change).
"""
switch_times(t, s) = [t[i] for i in 2:length(s) if s[i] != s[i-1]]

"""
    switches_per_cycle(t, s, f; t_from=1/f)

Number of valve switches per tail cycle, counted after `t_from` (the ramp).
"""
function switches_per_cycle(t, s, f; t_from=1/f)
    ts = switch_times(t, s)
    n = count(>=(t_from), ts)
    cycles = (t[end] - t_from) * f
    return cycles > 0 ? n / cycles : NaN
end

"Minimum gap between consecutive valve switches [s] (≥ min_dwell by construction)."
function min_switch_gap(t, s)
    ts = switch_times(t, s)
    length(ts) > 1 ? minimum(diff(ts)) : Inf
end
