# Live progress of a run: one updating terminal line + an atomically written
# JSON file `results/progress/<case>.json` (read by scripts/progress.jl).

mutable struct Progress
    case::String
    t_end::Float64
    file::String          # "" = no file
    tty::Bool
    io::IO
    wall0::Float64
    last_print::Float64
    last_file::Float64
    print_dt::Float64
    file_dt::Float64
    enabled::Bool
end

"""
    Progress(case, t_end; dir=joinpath(RESULTS_DIR,"progress"), io=stdout,
             print_dt=0.5, file_dt=1.0, enabled=true)

Progress reporter. `progress_update!(pr, t, steps; readouts...)` at every step (it
throttles itself), `progress_finish!(pr, status)` at the end.
"""
function Progress(case, t_end; dir=joinpath(RESULTS_DIR, "progress"), io=stdout,
                  print_dt=0.5, file_dt=1.0, enabled=true)
    file = ""
    if enabled && dir !== nothing
        mkpath(dir); file = joinpath(dir, "$(case).json")
    end
    tty = io isa Base.TTY
    pr = Progress(String(case), Float64(t_end), file, tty, io, time(), -Inf, -Inf,
                  print_dt, file_dt, enabled)
    return pr
end

_fmt_dur(s) = !isfinite(s) ? "?" : s < 60 ? @sprintf("%ds", round(Int, s)) :
              s < 3600 ? @sprintf("%dm%02ds", floor(Int, s / 60), round(Int, s % 60) % 60) :
              @sprintf("%dh%02dm", floor(Int, s / 3600), floor(Int, (s % 3600) / 60))

_json(x::AbstractString) = "\"" * replace(x, "\\" => "\\\\", "\"" => "\\\"") * "\""
_json(x::Real) = isfinite(x) ? @sprintf("%.6g", x) : "null"
_json(x::Integer) = string(x)
_json(x::Symbol) = _json(String(x))

function _write_json(pr::Progress, pct, t, steps, wall, eta, status, readouts)
    isempty(pr.file) && return
    parts = String[]
    push!(parts, "\"case\": " * _json(pr.case), "\"pct\": " * _json(pct),
          "\"t_phys\": " * _json(t), "\"t_end\": " * _json(pr.t_end),
          "\"steps\": " * _json(steps), "\"wall_s\": " * _json(wall),
          "\"eta_s\": " * _json(eta), "\"status\": " * _json(status),
          "\"updated\": " * _json(time()), "\"pid\": " * _json(getpid()))
    for (k, v) in pairs(readouts)
        v isa Real && push!(parts, _json(String(k)) * ": " * _json(v))
    end
    tmp = pr.file * ".tmp"
    open(tmp, "w") do f
        write(f, "{" * join(parts, ", ") * "}\n")
    end
    mv(tmp, pr.file; force=true)
end

"""
    progress_update!(pr::Progress, t, steps; force=false, readouts...)

Report progress at physical time `t` after `steps` CFD steps. Throttled:
terminal ≤ 1/print_dt per second, file ≤ 1/file_dt per second.
"""
function progress_update!(pr::Progress, t, steps; force=false, status="running", readouts...)
    pr.enabled || return
    now = time(); wall = now - pr.wall0
    pct = clamp(100 * t / pr.t_end, 0, 100)
    eta = t > 0 ? wall * (pr.t_end - t) / t : Inf
    if force || now - pr.last_print >= pr.print_dt
        sps = steps / max(wall, 1e-9)
        line = @sprintf("[%s] %5.1f %%  t=%.2f/%.2f s  steps/s=%.1f  ETA %s",
                        pr.case, pct, t, pr.t_end, sps, _fmt_dur(eta))
        if pr.tty
            print(pr.io, "\r", line, "\e[K"); flush(pr.io)
        else
            println(pr.io, line); flush(pr.io)
        end
        pr.last_print = now
    end
    if force || now - pr.last_file >= pr.file_dt
        _write_json(pr, pct, t, steps, wall, eta, status, readouts)
        pr.last_file = now
    end
    nothing
end

"Final report: status \"done\" or \"failed\"."
function progress_finish!(pr::Progress, t, steps, status; readouts...)
    pr.enabled || return
    progress_update!(pr, t, steps; force=true, status, readouts...)
    pr.tty && println(pr.io)
    println(pr.io, @sprintf("[%s] %s after %s wall, %d steps", pr.case, status,
                            _fmt_dur(time() - pr.wall0), steps))
    nothing
end
