# Render the stage-7 3D frames (results/frames/<case>/frame_NNNN.jls, written by
# scripts/stage7_3d.jl with FRAME_DT > 0) into an MP4 and a PNG screenshot.
#
#   julia --project=viz viz/render3d.jl <case> [fps]
#
# Wake: λ2 isosurface (vortex cores) at a fixed threshold, 2 % of the strongest wake core
# in the last frame (same rule as the stage-7 λ2 plot); λ2 within 3 cells of the skin (boundary
# layer) is hidden. Body: SDF = 0 isosurface. View cropped to the fish and the near wake.
# Outputs: results/<case>_3d.mp4, results/<case>_3d.png (last frame).

using GLMakie, Serialization, Printf

const CASE = length(ARGS) >= 1 ? ARGS[1] : "stage7_3d_n128_fin"
const FPS = length(ARGS) >= 2 ? parse(Int, ARGS[2]) : 25
const R = normpath(joinpath(@__DIR__, "..", "results"))
const FDIR = joinpath(R, "frames", CASE)

files = sort(filter(f -> endswith(f, ".jls"), readdir(FDIR; join=true)))
isempty(files) && error("no frames in $FDIR")
println("[render3d] $(length(files)) frames from $FDIR")

# physical coordinates [m] of the dumped (downsampled) cells; cell I has its centre at I - 1.5
function axes_phys(F)
    s, o, lf = F["stride"], F["origin"], F["lf"]
    ntuple(d -> [((2 + (i - 1) * s) - 1.5 - o[d]) * lf for i in 1:size(F["l2"], d)], 3)
end

# crop box [m]: nose to 0.3 m behind the tail tip, ±0.15 m sideways, ±0.08 m vertically
const BOX = ((-0.08, 0.45), (-0.15, 0.15), (-0.08, 0.08))
fl = deserialize(files[end])
xs, ys, zs = axes_phys(fl)
const IX = ntuple(d -> findall(v -> BOX[d][1] <= v <= BOX[d][2], (xs, ys, zs)[d]), 3)
xs, ys, zs = xs[IX[1]], ys[IX[2]], zs[IX[3]]
"Cropped -λ2 (skin layer zeroed) and -SDF of one frame."
function fields(F)
    l2 = F["l2"][IX...]; sd = F["sdf"][IX...]
    l2[sd .< 3] .= 0
    -l2, -sd
end
iw = findfirst(>(0.18), xs)                               # wake: 3 cm behind the tail tip
const THR = 0.02 * minimum(fl["l2"][IX...][iw:end, :, :])     # [1/s²], negative
@printf("[render3d] λ2 threshold %.3g 1/s²\n", THR)

GLMakie.activate!(visible=false)
fig = Figure(size=(1920, 1080), backgroundcolor=:white)
ax = Axis3(fig[1, 1]; aspect=:data, azimuth=-0.62π, elevation=0.16π,
           xlabel="x [m]", ylabel="y [m]", zlabel="z [m]", protrusions=40)
w0, b0 = fields(fl)
wake = Observable(w0)
body = Observable(b0)
xr, yr, zr = extrema(xs), extrema(ys), extrema(zs)
volume!(ax, xr, yr, zr, wake; algorithm=:iso, isovalue=-THR, isorange=-0.6THR,
        colormap=[RGBf(0.16, 0.50, 0.73), RGBf(0.16, 0.50, 0.73)])
volume!(ax, xr, yr, zr, body; algorithm=:iso, isovalue=0.0, isorange=1.0,
        colormap=[RGBf(0.75, 0.22, 0.17), RGBf(0.75, 0.22, 0.17)])
info = Observable("")
Label(fig[0, 1], info; fontsize=30, tellwidth=false)
Label(fig[2, 1], "WaterLily.jl 3D: fish with caudal fin, valve-driven tail 2 Hz, inflow 0.2 m/s. " *
      "Blue: vortex cores (λ2 < $(round(THR, sigdigits=2)) 1/s²), red: body";
      fontsize=20, color=:gray30, tellwidth=false)

function show!(F)
    w, b = fields(F)
    wake[] = w; body[] = b
    info[] = @sprintf("t = %.2f s    tail angle θ = %+.2f rad    Fx = %+.1f mN", F["t"], F["θ"], 1e3F["Fx"])
end

out = joinpath(R, "$(CASE)_3d.mp4")
record(fig, out, files; framerate=FPS) do f
    show!(deserialize(f))
end
show!(fl)
save(joinpath(R, "$(CASE)_3d.png"), fig)
println("[render3d] wrote $out and $(CASE)_3d.png")
