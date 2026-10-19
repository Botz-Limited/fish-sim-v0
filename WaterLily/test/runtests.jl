# Tests of the FishLily core (spec section 5).
# Run from WaterLily/:  julia --project=. -t 4 test/runtests.jl
using Test
using StaticArrays
using ForwardDiff
using WaterLily
using FishLily        # this project (WaterLily/Project.toml) is the FishLily package
using DataFrames: nrow

# bisection for the zero of f on [a, b] (f(a), f(b) of opposite signs)
function bisect(f, a, b; tol=1e-10)
    fa = f(a)
    for _ in 1:200
        m = (a + b) / 2; fm = f(m)
        (sign(fm) == sign(fa)) ? (a = m; fa = fm) : (b = m)
        b - a < tol && break
    end
    (a + b) / 2
end
"Half-thickness of the straight fish at x (upper surface y)."
find_zero_y(g, x) = bisect(y -> fish_sdf(g, x, y, 0.0), 0.0, 0.05)
"Lower and upper surface y of the bent fish along the vertical line x."
function bracket_surfaces(g, x, θ)
    ym = θ * bend_h(g, x)
    (bisect(y -> fish_sdf(g, x, y, θ), ym - 0.05, ym), bisect(y -> fish_sdf(g, x, y, θ), ym, ym + 0.05))
end
"Vertical half-distance between the bent surfaces at x."
surface_halfwidth(g, x, θ) = (b = bracket_surfaces(g, x, θ); (b[2] - b[1]) / 2)

@testset "FishLily" begin

@testset "valve" begin
    p = VALVE
    for f in (1.5, 2.0, 2.5)
        v = valve_series(f, 8.0)
        sw = switches_per_cycle(v.t, v.s, f)              # counted after the ramp (1 period)
        @test 1.8 <= sw <= 2.2
        @test min_switch_gap(v.t, v.s) >= p.min_dwell - 1e-9
        m = v.t .>= 2.0                                    # well after the ramp
        amp = (maximum(v.V_p[m]) - minimum(v.V_p[m])) / 2
        @test isapprox(amp, p.Q_const / (4f); rtol=0.15)   # triangle amplitude
        @test all(abs.(v.Q) .<= p.Q_const * (1 + 1e-12))
    end
    # rejection outside the range, no clamping
    @test_throws ArgumentError check_freq(1.4)
    @test_throws ArgumentError check_freq(2.6)
    @test_throws ArgumentError Valve(1.0)
    @test_throws ArgumentError valve_series(3.0, 1.0)
    @test check_freq(1.5) == 1.5 && check_freq(2.5) == 2.5
    # streaming stepper == whole-series function at the nodes, also with odd CFD steps
    vs = valve_series(2.0, 1.5)
    V = Valve(2.0)
    for t in 0.0:0.0037:1.5
        k = round(Int, t / DT_VALVE)
        if abs(t - k * DT_VALVE) < 1e-12
            @test valve_state(V, t).V_p ≈ vs.V_p[k+1]
        else
            st = valve_state(V, t)
            k0 = floor(Int, t / DT_VALVE + 1e-9)
            @test min(vs.V_p[k0+1], vs.V_p[k0+2]) - 1e-12 <= st.V_p <= max(vs.V_p[k0+1], vs.V_p[k0+2]) + 1e-12
        end
    end
    @test theta_kinematic(p.A_V) ≈ 0.4                    # A_V <-> 0.4 rad
    @test chamber_dp(1.0, 0.0) == p.p_max                  # relief valve clip
end

@testset "units" begin
    u = Units(128; U=1.0, Re=5000)
    for q in (:length, :velocity, :time, :frequency, :acceleration, :pressure, :force, :moment, :area, :nu)
        x = 0.123
        @test to_phys(u, q, to_grid(u, q, x)) ≈ x
        @test to_grid(u, q, to_phys(u, q, [x, 2x])) ≈ [x, 2x]
    end
    @test to_grid(u, :length, L_BODY) ≈ 128
    @test to_grid(u, :velocity, U_REF) ≈ 1
    @test to_phys(u, :time, 128.0) ≈ L_BODY / U_REF        # one convective time
    @test nu_grid(u) ≈ 128 / 5000
    @test nu_sim(u) ≈ U_REF * L_BODY / 5000
    @test coefficient(u, 0.5 * 128) ≈ 1
    @test force_coeff(u, 0.5 * 128) ≈ 1
end

@testset "geometry" begin
    g = FishGeom()
    # sign: inside / outside, straight and bent
    for θ in (0.0, 0.4, -0.4)
        @test fish_sdf(g, -0.03, 0.0, θ) < 0                 # head
        @test fish_sdf(g, 0.05, θ * bend_h(g, 0.05), θ) < 0   # tail on the midline
        @test fish_sdf(g, 0.14, θ * bend_h(g, 0.14), θ) < 0   # near tip
        @test fish_sdf(g, 0.10, θ * bend_h(g, 0.10) + 0.03, θ) > 0
        @test fish_sdf(g, -0.07, 0.0, θ) > 0                  # ahead of nose
        @test fish_sdf(g, 0.16, θ * bend_h(g, 0.16), θ) > 0   # behind tip
    end
    # nose and tip positions of the straight fish
    @test abs(fish_sdf(g, -HEAD_A, 0.0, 0.0)) < 1e-9
    @test abs(fish_sdf(g, L_TAIL, 0.0, 0.0)) < 1e-9
    @test abs(fish_sdf(g, 0.0, T_ROOT / 2, 0.0)) < 1e-9
    # thickness ≈ linear taper
    for x in (0.03, 0.08, 0.12)
        y = find_zero_y(g, x)
        @test isapprox(2y, tail_thickness(x); rtol=0.05)   # tangent-line taper of the uneven capsule: ≤ 4 % thinner than linear
    end
    # |∇sdf| ≈ 1 near the surface (within 2 mm), straight and bent
    for θ in (0.0, 0.3, 0.5), x in range(-0.055, 0.14; length=12), side in (-1, 1), off in (-0.002, 0.0015)
        y0 = θ * bend_h(g, x) + side * surface_halfwidth(g, x, θ)
        G = ForwardDiff.gradient(q -> fish_sdf(g, q[1], q[2], θ), [x, y0 + side * off])
        @test isapprox(sqrt(sum(abs2, G)), 1; atol=0.12)
    end
    # tail tip displacement = θ·h(1): midline (centre between the two surfaces) at the tip region
    for θ in (0.2, 0.4)
        @test tail_tip_displacement(θ) ≈ θ * bend_h(g, L_TAIL)
        x = L_TAIL - T_TIP                       # just before the rounded tip
        yl, yu = bracket_surfaces(g, x, θ)
        @test isapprox((yl + yu) / 2, θ * bend_h(g, x); atol=5e-4)
        @test isapprox(θ * bend_h(g, x), tail_tip_displacement(θ); atol=θ * T_TIP * 1.01)
    end
    # head does not move
    @test fish_sdf(g, -0.03, 0.01, 0.5) ≈ fish_sdf(g, -0.03, 0.01, 0.0)
    # AutoBody in grid units: sdf in cells, body velocity from θ̇
    u = Units(64)
    origin = (40.0, 50.0)
    θf = t -> 0.3 * sin(4π * t)
    body = fish_body(θf, u, origin; T=Float64)
    @test WaterLily.sdf(body, SVector(origin[1] - to_grid(u, :length, 0.03), origin[2]), 0.0) < 0
    xg = SVector(origin[1] + to_grid(u, :length, 0.13), origin[2] + 3.0)
    d_cells = WaterLily.sdf(body, xg, 0.0)
    @test d_cells ≈ to_grid(u, :length, fish_sdf(g, 0.13, to_phys(u, :length, 3.0), 0.0)) rtol = 1e-6
    # at t=0 θ̇ = 0.3·4π: lateral velocity of a midline point of the tail ≈ θ̇·h(x)
    xm = SVector(origin[1] + to_grid(u, :length, 0.12), origin[2])
    d, n, V = WaterLily.measure(body, xm, 0.0)
    Vy_phys = to_phys(u, :velocity, V[2])
    @test isapprox(Vy_phys, 0.3 * 4π * bend_h(g, 0.12); rtol=0.05)
end

@testset "CFD smoke (coarse)" begin
    t0 = time()
    # coarse circle: runs, finite, drag positive
    D = 16
    sim = Simulation((6D, 4D), (1f0, 0f0), D; ν=1f0 * D / 100,
                     body=AutoBody((x, t) -> sqrt(sum(abs2, x .- SA[1.5f0D, 2f0D])) - D / 2))
    sim_step!(sim, 2.0)
    F = body_force(sim)
    @test all(isfinite, F.F)
    @test F.F[1] > 0
    # coarse fish with the valve driver in still water, a few steps
    fs = make_fish_sim(; n=32, U_in=0.0, name="smoke", domain=DomainParams(0.5, 1.0, 0.75))
    df = run_fish!(fs, 0.05; driver=ValveDriver(2.0), progress=false)
    @test nrow(df) > 3
    @test all(isfinite, df.Fx) && all(isfinite, df.M)
    @test df.t[end] >= 0.05 - 1e-9
    @test all(diff(df.t) .> 0)
    @test all(abs.(df.θ) .<= 0.6)
    # force sign/scale: linear pressure p = y (grid) => force on the body = −area·ê_y
    fs2 = make_fish_sim(; n=64, U_in=0.0, name="hydro", domain=DomainParams(0.5, 0.5, 0.5))
    p = fs2.sim.flow.p
    for I in CartesianIndices(p); p[I] = WaterLily.loc(0, I, Float32)[2]; end
    g = FishGeom(); h = 1e-4
    area = sum(fish_sdf(g, x, y, 0.0) < 0 for x in -HEAD_A:h:L_TAIL, y in -0.02:h:0.02) * h^2
    F = body_force(fs2.sim).Fp
    @test isapprox(F[2], -to_grid(fs2.units, :area, area); rtol=0.03)
    @test abs(F[1]) < 0.03 * abs(F[2])
    @test time() - t0 < 30
end

@testset "box-restricted measure == full measure" begin
    # valve-driven tail; second case also moves the body (free-swimming-like X(t))
    for (U_in, moveX) in ((0.0, false), (0.2, true))
        res = map((false, true)) do box
            fs = make_fish_sim(; n=48, U_in, name="boxeq", box, X=moveX ? Track() : nothing,
                               domain=DomainParams(0.75, 1.0, 0.75))
            d = ValveDriver(2.0)
            rows = NamedTuple[]
            for _ in 1:30
                t0 = t_phys(fs); t1 = to_phys(fs.units, :time, Float64(sum(fs.sim.flow.Δt)))
                drive!(d, fs, t0, t1)
                moveX && set_track!(fs.X, t0, -0.5t0, t1, -0.5t1)
                sim_step!(fs.sim; remeasure=true)
                fs.sim.flow.Δt[end] = min(fs.sim.flow.Δt[end], 0.4f0)
                push!(rows, readouts(fs))
            end
            fl = fs.sim.flow
            (; rows, u=copy(fl.u), p=copy(fl.p), μ0=copy(fl.μ₀), μ1=copy(fl.μ₁), V=copy(fl.V),
               body=fs.sim.body)
        end
        full, boxed = res
        @test boxed.body isa BoxedBody && !(full.body isa BoxedBody)
        @test boxed.body.regrow[] == 0
        @test [r.Fx for r in boxed.rows] == [r.Fx for r in full.rows]
        @test [r.Fy for r in boxed.rows] == [r.Fy for r in full.rows]
        @test [r.M for r in boxed.rows] == [r.M for r in full.rows]
        @test boxed.u == full.u && boxed.p == full.p
        @test boxed.μ0 == full.μ0 && boxed.μ1 == full.μ1 && boxed.V == full.V
        @test boxed.body.box[] != CartesianIndices(full.p)   # really restricted
    end
end

end # testset
