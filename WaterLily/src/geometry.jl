# 2D fish geometry (top view) as a WaterLily `AutoBody` (SDF + coordinate map).
#
# Physical body frame (meters): nose at x = -HEAD_A, tail root at x = 0,
# tail tip at x = L_TAIL, axis y = 0.
#   head : half-ellipse, semi-axes HEAD_A (x) × HEAD_B (y), x ≤ 0
#   tail : tapered "uneven capsule": circle r = T_ROOT/2 at x = 0 and circle
#          r = T_TIP/2 at x = L_TAIL − T_TIP/2 joined by tangent lines, so the
#          thickness tapers (practically linearly) 0.030 -> 0.010 m and the
#          rounded tip ends exactly at x = L_TAIL (total length L_BODY).
#
# Bending (spec 3.2): tail midline y_m(x,t) = θ(t)·h(x), with uniform
# curvature over the chamber region [CH_X0, CH_X1] and straight elsewhere:
#   h(x)  = (u − x0)²/(2(x1 − x0)) + max(x − x1, 0),   u = clamp(x, x0, x1)
#   h'(x) = (u − x0)/(x1 − x0)          (slope; = 1 on the distal part)
# so θ is the tip slope angle (small-angle) and the tip displacement is θ·h(L_TAIL).
# The map inverts the midline: world point -> (foot point x_f on the midline,
# signed distance normal to the midline), using one Gauss–Newton step, so the
# thickness is measured NORMAL to the midline (small-angle, fine up to ~0.5 rad).
# The head (x < x0) is not moved by the map.

"""
    FishGeom{T}

Geometric constants of the fish in element type `T` (use the simulation's
`T`, e.g. Float32, to keep the WaterLily kernels type-stable).
"""
struct FishGeom{T}
    head_a::T
    head_b::T
    r_root::T
    r_tip::T
    x_tipc::T     # tip circle centre
    x0::T         # chamber start (bending region)
    x1::T         # chamber end
    l_tail::T
    clampdy::T    # max. lateral offset used in the foot-point step (keeps far field sane)
end
FishGeom(T::Type=Float64) = FishGeom{T}(HEAD_A, HEAD_B, T_ROOT/2, T_TIP/2, L_TAIL - T_TIP/2,
                                        CH_X0, CH_X1, L_TAIL, T_ROOT)

"Bending shape function h(x) [m] (x from the tail root, meters)."
@inline function bend_h(g::FishGeom, x)
    u = clamp(x, g.x0, g.x1)
    (u - g.x0)^2 / (2 * (g.x1 - g.x0)) + max(x - g.x1, zero(x))
end
"Slope dh/dx [-]."
@inline bend_dh(g::FishGeom, x) = (clamp(x, g.x0, g.x1) - g.x0) / (g.x1 - g.x0)

"Tail tip lateral displacement θ·h(L_TAIL) [m] for a bending angle θ [rad]."
tail_tip_displacement(θ, g::FishGeom=FishGeom()) = θ * bend_h(g, g.l_tail)

"Tail thickness of the straight tail at x [m] (≈ linear taper 0.030 -> 0.010 m)."
tail_thickness(x) = T_ROOT + (T_TIP - T_ROOT) * x / L_TAIL

# --- signed distance of the STRAIGHT fish, physical units -------------------------
@inline function _ellipse_sdf(x, y, a, b)
    # Distance to an ellipse by the fixed-point iteration on the closest point
    # (evolute method, "a simple iterative method" by L. Mayer / 0xfaded),
    # 4 iterations ≈ exact. The first-order k0(k0-1)/k1 formula was too poor
    # near the slender nose (|∇sdf| up to 1.18 at 2 mm, see NOTES.md).
    px, py = abs(x), abs(y)
    tx = ty = one(px) / sqrt(2 * one(px))
    c = a^2 - b^2
    for _ in 1:4
        ex = c * tx^3 / a; ey = -c * ty^3 / b
        rx = a * tx - ex; ry = b * ty - ey
        qx = px - ex; qy = py - ey
        r = sqrt(rx^2 + ry^2); q = sqrt(qx^2 + qy^2)
        tx = clamp((qx * r / q + ex) / a, zero(px), one(px))
        ty = clamp((qy * r / q + ey) / b, zero(px), one(px))
        t = sqrt(tx^2 + ty^2); tx /= t; ty /= t
    end
    dist = sqrt((px - a * tx)^2 + (py - b * ty)^2)
    ifelse((px / a)^2 + (py / b)^2 < 1, -dist, dist)
end

@inline function _uneven_capsule_sdf(x, y, r1, r2, h)
    # axis along +x from (0,0) radius r1 to (h,0) radius r2 (iq, exact)
    px, py = abs(y), x
    b = (r1 - r2) / h
    a = sqrt(1 - b^2)
    k = -b * px + a * py
    d1 = sqrt(px^2 + py^2) - r1
    d2 = sqrt(px^2 + (py - h)^2) - r2
    d3 = a * px + b * py - r1
    ifelse(k < 0, d1, ifelse(k > a * h, d2, d3))
end

"""
    fish_sdf_straight(g, x, y)

Signed distance [m] of the straight fish at body-frame point (x, y) [m];
negative inside.
"""
@inline function fish_sdf_straight(g::FishGeom, x, y)
    head = max(_ellipse_sdf(x, y, g.head_a, g.head_b), x)   # half-ellipse x ≤ 0
    tail = _uneven_capsule_sdf(x, y, g.r_root, g.r_tip, g.x_tipc)
    min(head, tail)
end

"""
    bend_inverse(g, x, y, θ) -> (xr, yr)

Map a body-frame point (x, y) [m] of the bent fish (tip angle θ) back to the
straight reference frame: foot point on the midline and normal offset.
"""
@inline function bend_inverse(g::FishGeom, x, y, θ)
    ym = θ * bend_h(g, x); m = θ * bend_dh(g, x)
    dy = clamp(y - ym, -g.clampdy, g.clampdy)
    xf = x + m * dy / (1 + m^2)                       # one Gauss–Newton step to the foot point
    ymf = θ * bend_h(g, xf); mf = θ * bend_dh(g, xf)
    yr = ((y - ymf) - mf * (x - xf)) / sqrt(1 + mf^2) # distance normal to the tangent at x_f
    return xf, yr
end

"Signed distance [m] of the fish bent by θ at body-frame point (x, y) (pseudo-SDF, exact on the midline normal)."
@inline fish_sdf(g::FishGeom, x, y, θ) = fish_sdf_straight(g, bend_inverse(g, x, y, θ)...)

"""
    fish_body(θ, units, origin; X=nothing, T=Float32) -> AutoBody

WaterLily body of the fish.

- `θ`      : function `θ(t_phys)` [rad] of the tail bending angle (any callable,
             e.g. `t -> 0.3sin(4πt)`, a `Track`, or `t -> 0.0` for a rigid fish).
             Must accept ForwardDiff duals (plain arithmetic is fine): the body
             velocity is obtained by differentiating the map in time.
- `units`  : `Units` (grid <-> physical).
- `origin` : grid coordinates (cells) of the tail root when X = 0.
- `X`      : optional function `X(t_phys)` [m], body x-offset (free swimming:
             the body moves through the water in +x for X > 0). `nothing` = fixed.

- `box`    : `true` (default) wraps the AutoBody in a [`BoxedBody`](@ref): the body is
             measured (and the forces integrated) only in a grid box around the fish
             that follows θ(t) and X(t) – identical results, much faster for a
             moving tail. `false` returns the plain `AutoBody` (full-domain measure).

The map returns physical reference-frame coordinates [m]; the sdf returns
grid cells, so WaterLily's chain rule gives correct normals and velocities.
"""
function fish_body(θ, units::Units, origin; X=nothing, T::Type=Float32, box=true)
    g = FishGeom(T)
    ox, oy = T(origin[1]), T(origin[2])
    lf = T(unit_factor(units, :length))     # m per cell
    tf = T(unit_factor(units, :time))       # s per grid time unit
    inv_lf = inv(lf)
    Xf = X === nothing ? (t -> zero(t)) : X
    map = (x, t) -> begin
        tp = t * tf
        xb = (x[1] - ox) * lf - Xf(tp)
        yb = (x[2] - oy) * lf
        xr, yr = bend_inverse(g, xb, yb, θ(tp))
        SVector(xr, yr)
    end
    sdf = (ξ, t) -> fish_sdf_straight(g, ξ[1], ξ[2]) * inv_lf
    body = AutoBody(sdf, map)
    box || return body
    # grid box of the fish at grid time t (+ `pad` cells): x from nose to tip
    # (+ the small x-shift of the bent tip), y from the straight axis to the
    # bent tip, ± the root half-thickness. Cell I has centre loc = I − 1.5.
    # (names prefixed with b_: plain locals here would be shared with the
    # `map` closure above, e.g. its `xb`, and get boxed)
    b_hL = Float64(bend_h(g, g.l_tail)); b_r = Float64(g.r_root)
    b_xn, b_xt = -Float64(g.head_a), Float64(g.l_tail)
    b_lf, b_tf = Float64(lf), Float64(tf)
    b_o = (Float64(origin[1]), Float64(origin[2]))
    boxfun = let hL = b_hL, r = b_r, xn = b_xn, xt = b_xt, lfb = b_lf, tfb = b_tf, o = b_o, θ = θ, Xf = Xf
        (t, pad) -> begin
            tq = Float64(t) * tfb
            θt = Float64(θ(tq)); Xt = Float64(Xf(tq))
            ex = abs(θt) * r
            x0 = o[1] + (Xt + xn - ex) / lfb; x1 = o[1] + (Xt + xt + ex) / lfb
            y0 = o[2] + (min(0.0, θt * hL) - r) / lfb; y1 = o[2] + (max(0.0, θt * hL) + r) / lfb
            CartesianIndices((floor(Int, x0 + 1.5) - pad:ceil(Int, x1 + 1.5) + pad,
                              floor(Int, y0 + 1.5) - pad:ceil(Int, y1 + 1.5) + pad))
        end
    end
    BoxedBody(body, boxfun)
end

"""
    Track(; t0=0, v0=0, rate=0)

Mutable, piecewise-linear signal `v(t) = v0 + rate·(t − t0)` (t physical).
Used as θ(t) or X(t) of a body driven step by step from a CFD loop:
before each CFD step set it with `set_track!(tr, t0, v0, t1, v1)`, so the
body position at t1 and its velocity over the step are consistent.
"""
mutable struct Track
    t0::Float64
    v0::Float64
    rate::Float64
end
Track(; t0=0.0, v0=0.0, rate=0.0) = Track(t0, v0, rate)
(tr::Track)(t) = tr.v0 + tr.rate * (t - tr.t0)
function set_track!(tr::Track, t0, v0, t1, v1)
    tr.t0 = t0; tr.v0 = v0
    tr.rate = t1 > t0 ? (v1 - v0) / (t1 - t0) : 0.0
    tr
end
