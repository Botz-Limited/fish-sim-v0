# Live table of all runs that report to results/progress/*.json
# (written by FishLily.run_fish! and the stage scripts).
#
#   julia scripts/progress.jl            refresh every 1 s, exit when no run is "running"
#   julia scripts/progress.jl --once     print once and exit
#   julia scripts/progress.jl --dir D    another progress directory
#
# No packages needed (tiny JSON reader for the flat files we write).
using Printf

function parse_flat_json(s)
    d = Dict{String,Any}()
    for m in eachmatch(r"\"([^\"]+)\"\s*:\s*(\"(?:[^\"\\]|\\.)*\"|[-+0-9.eE]+|null|true|false)", s)
        k, v = m.captures
        d[k] = startswith(v, "\"") ? unescape_string(v[2:end-1]) :
               v == "null" ? NaN : v == "true" ? true : v == "false" ? false : parse(Float64, v)
    end
    d
end

fmt_dur(s) = !(s isa Real) || !isfinite(s) ? "?" : s < 60 ? @sprintf("%ds", round(Int, s)) :
             s < 3600 ? @sprintf("%dm%02ds", floor(Int, s / 60), floor(Int, s % 60)) :
             @sprintf("%dh%02dm", floor(Int, s / 3600), floor(Int, (s % 3600) / 60))

function bar(pct; w=30)
    k = clamp(round(Int, w * pct / 100), 0, w)
    "[" * "#"^k * "."^(w - k) * "]"
end

num(d, k) = (v = get(d, k, NaN); v isa Real ? Float64(v) : NaN)

function table(dir)
    files = sort(filter(f -> endswith(f, ".json"), readdir(dir; join=true)))
    rows = Dict{String,Any}[]
    for f in files
        try
            push!(rows, parse_flat_json(read(f, String)))
        catch
        end
    end
    lines = String[]
    push!(lines, @sprintf("%-26s %-32s %6s %16s %8s %8s %-8s %s", "case", "progress", "pct", "t / t_end", "wall", "ETA",
                          "status", "readouts"))
    now = time()
    for r in rows
        st = get(r, "status", "?")
        stale = st == "running" && now - num(r, "updated") > 60     # no update for a minute: crashed?
        ro = String[]
        for k in ("s", "V_p", "θ", "Fx", "Cd", "Cl")
            v = num(r, k); isfinite(v) && push!(ro, @sprintf("%s=%.3g", k, v))
        end
        push!(lines, @sprintf("%-26s %-32s %5.1f%% %7.2f/%-7.2f %8s %8s %-8s %s", get(r, "case", "?"),
                              bar(num(r, "pct")), num(r, "pct"), num(r, "t_phys"), num(r, "t_end"),
                              fmt_dur(num(r, "wall_s")), st == "running" ? fmt_dur(num(r, "eta_s")) : "-",
                              stale ? "stale?" : st, join(ro, " ")))
    end
    lines, rows
end

function main(args)
    once = "--once" in args
    i = findfirst(==("--dir"), args)
    dir = i === nothing ? joinpath(@__DIR__, "..", "results", "progress") : args[i+1]
    isdir(dir) || (println("no progress directory: $dir"); return)
    tty = stdout isa Base.TTY
    while true
        lines, rows = table(dir)
        tty && !once && print("\e[H\e[2J")           # clear screen
        println(join(lines, "\n"))
        once && return
        running = any(r -> get(r, "status", "") == "running" && time() - num(r, "updated") <= 60, rows)
        running || (println("no running case – exiting"); return)
        sleep(1.0)
    end
end

main(ARGS)
