# viz/: visualisation for the WaterLily fish demo

`FishViz` draws any 2D `WaterLily.Simulation`: the vorticity field, the body as a solid shape,
a panel of live readouts and an optional force arrow. It can render in three ways:

| What | Function | Backend | Output |
|---|---|---|---|
| Video | `record_vorticity(sim, step!, readouts; duration, frame_dt, ...)` | CairoMakie (no display needed) | MP4, progress % printed to the terminal |
| Image | `snapshot(sim, path; readouts, ...)` | CairoMakie | PNG |
| Live window | `LiveViewer(sim; t_end, ...)` + `update!(viewer, sim, readouts)` | GLMakie | window with a progress bar and ETA; falls back to terminal progress when there is no display |

The live viewer is the main feature: the core run loop pushes frames into it while the
simulation computes. For the fish model see "The fish" below (`FishLive.jl`, `scripts/live.jl`,
`FISH_LIVE=1`, `scripts/animate.jl`).

The module does not depend on the fish model. The stand-in demo is a heaving and pitching
ellipse, built with `AutoBody` and a sinusoidal map.

## Environment

`viz/` has its own Julia environment, so the main `Project.toml` stays free of Makie:
WaterLily 1.9.2 (the same version as the main env), Makie 0.24.16, CairoMakie 0.15.16,
GLMakie 0.13.16, StaticArrays and Printf. It uses Julia 1.13.2.

```sh
julia -t 4 --project=viz -e 'using Pkg; Pkg.instantiate()'     # first time: about 2.5 min precompile
julia -t 4 --project=viz viz/demo_standin.jl                    # video + PNG + live window
julia -t 4 --project=viz viz/demo_standin.jl --no-live          # video + PNG only
julia -t 4 --project=viz viz/demo_standin.jl --no-record        # live window only
```

The demo writes `viz/out/standin.mp4` (1280×720, 30 fps, 7.5 s, 0.4 MB),
`viz/out/standin_snapshot.png` and `viz/out/viewer_screenshot.png`.

`FishLily` (the main project, `..`) is `Pkg.develop`ed into this environment (done once:
`julia --project=viz -e 'using Pkg; Pkg.develop(path=".")'` from `WaterLily/`), so
`julia --project=viz` can `using FishLily`. All packages the two manifests share have
identical versions, which is what makes the other direction work too: a script started
with `--project=.` loads the viewer lazily by appending `viz/` to `LOAD_PATH`
(`FishLily.maybe_live_hook`, below). After changing FishLily's dependencies run
`julia --project=viz -e 'using Pkg; Pkg.resolve()'`.

## The fish: live window, FISH_LIVE=1, MP4 (`FishLive.jl`)

`viz/FishLive.jl` binds FishViz to FishLily: readouts t, f, U_in, valve s, V_p [ml],
θ [deg], Fx, Fy, thrust [N/m] (instantaneous) and the thrust averaged over the last tail
period, plus the total force arrow (N/m, auto-scaled) at the fish centroid. Plot
coordinates are x/L, y/L with the tail root at (0, 0). In still water the view is zoomed
on the fish (x/L ∈ [-0.7, 2.3], y/L ∈ [-1, 1]); with inflow the whole domain is shown.

Live window on a case (window on the primary monitor, DP-2; terminal shows the progress line):

```sh
cd WaterLily
julia --project=. -t 2 scripts/live.jl --case tethered --f 2 --U 0 --n 128 --t 6
julia --project=. -t 2 scripts/live.jl --case tethered --f 2 --U 0.2 --t 4 --keep
julia --project=. -t 2 scripts/live.jl --case rigid --U 0.2 --t 4
julia --project=. -t 2 scripts/live.jl --case sine --f 2 --amp 20 --t 4
```

Any stage script, without editing it: every `run_fish!` call opens the window when
`FISH_LIVE=1` is set (and no `on_frame` is passed); the window of the previous run is
closed when the next run starts.

```sh
FISH_LIVE=1 julia --project=. -t 2 scripts/stage2_<name>.jl
FISH_LIVE=1 FISH_LIVE_KEEP=1 julia ...      # keep each window open until you close it
FISHVIZ_MONITOR=HDMI-A-1 FISH_LIVE=1 ...    # another monitor
```

A script with its own loop (not `run_fish!`) needs one line to get the hook, which is
`nothing` unless FISH_LIVE=1:

```julia
hook = maybe_live_hook(fs, t_end; driver)          # FishLily, no Makie dependency
# in the loop after each step (throttled to 5 fps by itself):
hook === nothing || hook(fs.sim, row)              # row: NamedTuple with t, s, V_p, θ, Fx, Fy, thrust
live_finish!(hook)                                  # final frame (no-op for nothing)
```

or pass it to `run_fish!(fs, t_end; driver, on_frame=hook, frame_every=1)`.

The first window takes 30–50 s to appear (loading GLMakie/CairoMakie and compiling the
draw path); later runs in the same process open in about a second.

Headless MP4 (no display needed):

```sh
julia --project=. -t 2 scripts/animate.jl              # -> results/fish_tethered_f2.mp4
julia --project=. -t 2 scripts/animate.jl --U 0.2      # -> results/fish_tethered_f2_U0.2.mp4
```

It simulates the start-up (valve transient, 2 s) without frames, then records 3 tail
periods at 100 frames per period (1280×720, 30 fps, 10 s of video).

## API

```julia
include("viz/FishViz.jl"); using .FishViz

readouts = sim -> (t=(t_phys(sim),"s"), f=(2.0,"Hz"), s=valve_state, V_p=(Vp_ml,"ml"),
                   θ=(θ_deg,"deg"), _1="", Fx=(Fx,"N"))   # NamedTuple: value, (value,"unit"), string, nothing
arrow    = sim -> (F=(Fx, Fy),)            # optional; add at=(x,y) in plot units (x/L); default = body centroid

# video (headless). step!(sim, t_target) must advance until time_of(sim) ≥ t_target
record_vorticity(sim, step!, readouts; duration=5.0, frame_dt=0.02, fps=30, time_of=t_phys, time_unit="s",
                 path="results/fish.mp4", clims=(-10,10), arrow, arrow_unit="N", title="...")
snapshot(sim, "results/fish.png"; readouts, arrow, time_of=t_phys, time_unit="s")

# live, driven by the core run loop
v = LiveViewer(sim; t_end=5.0, time_of=t_phys, time_unit="s", title="fish, f = 2 Hz", arrow, clims=(-10,10))
hook = on_frame(v)                       # (sim, readouts) -> Bool (true if a frame was drawn)
while t_phys(sim) < 5.0
    sim_step!(sim; remeasure=true)       # + valve/ODE update etc.
    hook(sim, readouts)                  # safe to call every step: throttled to max_fps (default 5)
end
finish!(v, sim, readouts)                # forced final frame, status "done" (or status="failed: ...")
screenshot(v, "results/viewer.png")      # optional
wait_close(v)                            # optional: keep the window until the user closes it
```

`run_live(sim, step!, readouts; t_end, frame_dt, ...)` is a standalone driver that opens a
viewer and steps the simulation itself.

Shared keywords (`FlowPanel`):

- `clims`: limits of the ω·L/U colour scale. The default is (-10, 10).
- `colormap`: the default is `:balance`.
- `stride` or `max_px`: downsampling. The live viewer uses at most 384 samples on the longer
  side; the recorder uses at most 1024.
- `origin`: the grid cell placed at x = y = 0.
- `xlims`, `ylims`: crop, in plot units.
- `size`: the default is (1280, 720).
- `body_color`.
- `arrow_scale`: `:auto` maps the 90th percentile of |F| over the last 100 frames to
  `arrow_len` = 0.6 L, capped at 2·`arrow_len`. A number gives a fixed scale in plot units per
  force unit.
- `arrow_unit`, `arrow_color`.
- `fontsize`: the default is 15.

`LiveViewer` keywords:

- `max_fps`: the default is 5.
- `headless`: the default is `!has_display()`.
- `window_title`.
- `print_every`: how often headless progress is printed. The default is 2 s.
- `monitor`: see below.

Plot coordinates are x/L and y/L: grid cells divided by `sim.L`, shifted by `origin`.
Vorticity is shown as ω·L/U, using `sim.L` and `sim.U`. Body time is `WaterLily.time(sim)`, in
grid units.

## Multi-monitor placement

The window is created hidden. It is then centred on the primary monitor's work area, shrunk to
fit within 90 % of it if needed, and only then shown. To use another output, set
`FISHVIZ_MONITOR=<name>` (for example `HDMI-A-1`), or pass the `monitor=` keyword.
`FishViz.monitors()` lists the monitors GLFW sees.

GLFW runs through XWayland on Linux (platform X11), so KWin honours the requested position.

This was verified on the KDE Plasma Wayland desktop with 3 monitors:

- Primary DP-2 (work area 2400,0, 2560×1440) gives window position (2880, 270) with size
  1600×900. That size is 1280×720 × 1.25 scale.
- A full-desktop capture (spectacle) confirmed that the window was on the middle monitor
  (DP-2), centred.
- `FISHVIZ_MONITOR=HDMI-A-1` gives (400, 225), centred on the left monitor.

No KWin rule was needed.

## Timings

Measured on this machine (4 threads, shared with other jobs, so ±20 %).

| Item | Time |
|---|---|
| `using` FishViz (loads WaterLily, CairoMakie, GLMakie) | about 5 s |
| First window: open and compile the GL draw path | about 7 s (one-off per process) |
| MP4: render and encode with CairoMakie, 1280×720 | 65–70 ms per frame (~15 fps), plus simulation time |
| PNG snapshot | 0.6 s |
| Live frame: fields + readouts + GL draw (field at most 384 px) | 10–15 ms per drawn frame, of which field extraction is ~4 ms |

Live-viewer overhead on the whole run, measured with `update!` called every step:

| Case | Overhead |
|---|---|
| Stand-in, 288×144 cells, 3.9 ms per step | +4–6 % at 5 fps |
| 576×288 cells, ~9 ms per step | +7 % at 4 fps, +12 % at 8 fps |

Headless progress-only mode costs less than 1 %.

The overhead is about `max_fps` × 12 ms per second of wall time, and it does not depend on the
CFD grid size apart from computing the vorticity (`curl`) once over the full grid. Larger fish
grids therefore have a smaller relative overhead.

## Caveats

- **The live drawing is synchronous.** GLMakie's background renderloop is replaced: frames are
  drawn inside `update!` on the calling thread through GLMakie internals (`pollevents`,
  `poll_updates`, `render_frame`, `SwapBuffers`), tested with GLMakie 0.13.16. The stock fps
  renderloop busy-waits on its timer whenever the simulation task yields, which cost about
  50 ms per frame. Consequences:
  - The window only processes events (move, resize, close) when a frame is drawn, which is
    `max_fps` times per second, so it can feel sluggish.
  - Call `update!` and the hook only from the main thread.
  - If GLMakie is upgraded and these internals change, `render_now!` in `viewer.jl` is the only
    place to fix.
- **Vorticity is computed into a private buffer.** `FishViz` never writes to `sim.flow.σ`.
  The body is drawn from `sdf(body, x, WaterLily.time(sim))`, evaluated on the CPU at the
  sample points. This also works for GPU simulations if the body's `sdf` and `map` are
  CPU-callable. Vorticity is computed on the device and copied back.
- **Without a display, GLMakie is not loaded at all.** GLFW fails in `__init__` without
  `DISPLAY`/`WAYLAND_DISPLAY`. `LiveViewer` then prints
  `[live]  37.2 %  t=1.86/5.00 s  ETA 2m10s` lines instead of drawing. CairoMakie video and
  PNG output work headless.
- **Glyph support depends on system fonts.** The readout panel uses a monospace system font
  (DejaVu Sans Mono, Noto Sans Mono, Liberation Mono, ...), with Makie's default font as a
  fallback. The `θ` label needs a font that has the glyph.
- **The panel has room for about 14 readout lines.** Use `_1 = ""` keys for blank spacer
  lines; `nothing` values are skipped.
- **2D only.** For 3D, use WaterLily's own `viz!` from WaterLilyMakieExt.
- **WaterLily's `update!` is extended.** `FishViz` adds a method to `WaterLily.update!` (for
  `LiveViewer`), so both can be `using`'d without a name clash.
- **Output is not deterministic across runs.** Recorded videos and timings depend on machine
  load.
