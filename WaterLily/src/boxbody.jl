# Box-restricted body measurement (performance).
#
# WaterLily's `measure!(flow, body)` evaluates the SDF over the WHOLE domain
# every step (`measure_sdf!`) and then fills μ₀, μ₁, V in a narrow band
# |d| < 2+ϵ. For the moving fish (≈ 1 % of the cells) that full-domain pass
# plus the full-domain force integrals dominated the step time.
#
# `BoxedBody` wraps any body together with a function giving a grid box
# (CartesianIndices) that contains the body plus its whole BDIM band at time t.
# `WaterLily.measure!` is specialised for it and
#   1. resets μ₀ = 1, μ₁ = 0, V = 0 (the far-field values) only on the union of
#      the previous and the new box (so cells the body has LEFT are cleaned,
#      e.g. free swimming),
#   2. measures the SDF only inside the new box (into flow.σ, as WaterLily),
#   3. fills μ₀, μ₁, V inside the new box with exactly WaterLily's code,
#   4. applies the same boundary conditions as WaterLily.
# Outside the box every cell keeps its far-field value, which is what the full
# measure gives there (d² ≥ (2+ϵ)², d > 0). Self-check: if any cell on the edge
# of the box is still inside the band (σ² < (2+ϵ)² or σ < 0), the padding is
# doubled and the measurement repeated, so a too-small box can never silently
# cut the body.
#
# `WaterLily.bbox(body, R)` (the hook WaterLily's force integrals already use)
# returns the box ∩ R, so `pressure_force`, `viscous_force`, `total_force` and
# FishLily's tail integrals also only loop over the box. Outside it the
# kernel-weighted normal `nds` is exactly zero, so the results are identical.
#
# Note: flow.σ is only valid inside the box after measure!, but WaterLily uses
# σ purely as scratch (conv_diff!, CFL), so nothing reads it elsewhere.
# CPU only as written (the Refs are fine for the KernelAbstractions CPU backend).

"""
    BoxedBody(body, boxfun; pad=4)

Wrap `body` so that `WaterLily.measure!` and the force integrals only touch a
box of the grid. `boxfun(t, pad)` -> `CartesianIndices` (cell indices, any
size, it is clipped to the domain) that must contain all cells with
d < 2+ϵ+pad at grid time `t` (`pad` in cells, the band is added by the caller).
`unbox(b)` returns the wrapped body.
"""
struct BoxedBody{B<:WaterLily.AbstractBody,F,C} <: WaterLily.AbstractBody
    body::B
    boxfun::F
    box::Base.RefValue{C}        # current box (clipped to the inside of the domain)
    measured::Base.RefValue{Bool}
    pad::Base.RefValue{Int}      # padding in cells beyond the BDIM band (grows on a failed self-check)
    regrow::Base.RefValue{Int}   # number of times the self-check had to grow the box
end
function BoxedBody(body::WaterLily.AbstractBody, boxfun; pad=4, N=2)
    C = CartesianIndices{N,NTuple{N,UnitRange{Int}}}
    box0 = CartesianIndices(ntuple(_ -> 1:0, N))
    BoxedBody{typeof(body),typeof(boxfun),C}(body, boxfun, Ref(box0), Ref(false), Ref(Int(pad)), Ref(0))
end

"The wrapped body (identity for any other body)."
unbox(b::BoxedBody) = b.body
unbox(b) = b

WaterLily.measure(b::BoxedBody, x, t; fastd²=Inf) = WaterLily.measure(b.body, x, t; fastd²)
WaterLily.sdf(b::BoxedBody, x, t=0; kwargs...) = WaterLily.sdf(b.body, x, t; kwargs...)
WaterLily.bbox(b::BoxedBody, R) = b.measured[] ? _intersect(R, b.box[]) : R

_intersect(A::CartesianIndices{N}, B::CartesianIndices{N}) where N =
    CartesianIndices(ntuple(i -> max(first(A.indices[i]), first(B.indices[i])):min(last(A.indices[i]), last(B.indices[i])), N))
_hull(A::CartesianIndices{N}, B::CartesianIndices{N}) where N =
    isempty(A) ? B : isempty(B) ? A :
    CartesianIndices(ntuple(i -> min(first(A.indices[i]), first(B.indices[i])):max(last(A.indices[i]), last(B.indices[i])), N))
_grow(A::CartesianIndices{N}, k) where N = CartesianIndices(ntuple(i -> first(A.indices[i])-k:last(A.indices[i])+k, N))

# true if some cell on a face of `box` that is not a face of the domain `R`
# is still inside the band (or the body)
function _edge_touches(σ, box::CartesianIndices{N}, R::CartesianIndices{N}, d²) where N
    T = eltype(σ)
    for i in 1:N, side in (1, 2)
        r = box.indices[i]
        k = side == 1 ? first(r) : last(r)
        k == (side == 1 ? first(R.indices[i]) : last(R.indices[i])) && continue  # domain edge
        face = CartesianIndices(ntuple(j -> j == i ? (k:k) : box.indices[j], N))
        mapreduce(I -> (σ[I]^2 < d²) | (σ[I] < zero(T)), |, face; init=false) && return true
    end
    false
end

function WaterLily.measure!(a::WaterLily.AbstractFlow{N,T}, b::BoxedBody; t=zero(T), ϵ=1) where {N,T}
    body = b.body
    d² = T(2 + ϵ)^2
    R = WaterLily.inside(a.p)
    full = CartesianIndices(a.p)
    local box
    while true
        box = _intersect(R, b.boxfun(t, ceil(Int, 2 + ϵ) + b.pad[]))
        WaterLily.@loop _sdf!(a.σ, body, I, t, d²) over I ∈ box
        _edge_touches(a.σ, box, R, d²) || break
        box == R && break
        b.pad[] *= 2; b.regrow[] += 1
    end
    # reset to the far field on the old ∪ new box (+1 ghost layer, clipped)
    if b.measured[]
        rz = _intersect(full, _grow(_hull(b.box[], box), 1))
        WaterLily.@loop _reset!(a.μ₀, a.μ₁, a.V, I) over I ∈ rz
    else
        a.V .= zero(T); a.μ₀ .= one(T); a.μ₁ .= zero(T)
    end
    @fastmath @inline function fillb!(μ₀, μ₁, V, d, I)   # verbatim WaterLily 1.9.2 Body.jl
        if d[I]^2 < d²
            for i ∈ 1:N
                dᵢ, nᵢ, Vᵢ = WaterLily.measure(body, WaterLily.loc(i, I, T), t, fastd²=d²)
                dᵢ = abs(dᵢ) ≤ 0.5 ? dᵢ : copysign(dᵢ, d[I])
                V[I, i] = Vᵢ[i]
                μ₀[I, i] = WaterLily.μ₀(dᵢ, ϵ)
                for j ∈ 1:N
                    μ₁[I, i, j] = WaterLily.μ₁(dᵢ, ϵ) * nᵢ[j]
                end
            end
        elseif d[I] < zero(T)
            for i ∈ 1:N
                μ₀[I, i] = zero(T)
            end
        end
    end
    WaterLily.@loop fillb!(a.μ₀, a.μ₁, a.V, a.σ, I) over I ∈ box
    b.box[] = box; b.measured[] = true
    WaterLily.BC!(a.μ₀, zeros(SVector{N,T}), false, a.perdir)
    WaterLily.BC!(a.V, zeros(SVector{N,T}), a.exitBC, a.perdir)
end

@inline _sdf!(σ, body, I, t, d²) = (σ[I] = WaterLily.sdf(body, WaterLily.loc(0, I, eltype(σ)), t; fastd²=d²))

@inline function _reset!(μ₀::AbstractArray{T}, μ₁, V, I::CartesianIndex{N}) where {T,N}
    for i in 1:N
        μ₀[I, i] = one(T); V[I, i] = zero(T)
        for j in 1:N
            μ₁[I, i, j] = zero(T)
        end
    end
end
