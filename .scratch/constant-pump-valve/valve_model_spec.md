# Wspólny model: pompa o stałych obrotach + zawory kierunkowe (±1)

Decyzje użytkownika (2026-10-13):
- Pompa ma STAŁE obroty i stały wydatek `Q_const`. Kierunek przepływu wybierają zawory.
- Zawory mają TYLKO dwa stany: `s = +1` (R→L) albo `s = −1` (L→R). Brak stanu zamkniętego.
  `u = 0` zostaje wyłącznie jako "pompa wyłączona" (brak rytmu / silnik stoi), nie jako stan zaworu.
- Parametry (wszystkie PLACEHOLDER w configu):
  - `Q_const` = dotychczasowa wartość `Q_max` w danej gałęzi (zastępuje `Q_max`),
  - `tau_valve` = 0.02 s (zastępuje `tau_pump`): czas przełączenia zaworu + odwrócenie strumienia,
  - `valve_hysteresis` = δ = 1 ml (1e-6 m³) – histereza regulatora przekaźnikowego.

## Hydraulika
    dQ/dt = (s·Q_const − Q) / tau_valve
Reszta (komory, Δp, zawór przelewowy, zachowanie sumy V_L+V_R) bez zmian.

## Sterowanie (zastępuje feed-forward + P i ewentualny człon τ·d²V_ref/dt²)
V_ref(t) zostaje jak było (rampa, bias na skręt, set_freq bez skoku fazy).
Regulator przekaźnikowy z histerezą, stan `s` pamiętany między krokami:
    e = V_ref − V_p
    if e >  δ: s = +1
    if e < −δ: s = −1
    (w przeciwnym razie s bez zmian)
Start: s = +1. Reset symulacji przywraca s = +1.
Nie ma już `K_v` (usuń z configu).

## Fizyka do pokazania w README
- Dopóki 2πf·A_V < Q_const, regulator śledzi V_ref "piłą" (częste przełączanie, pasmo ≈ ±δ plus
  przerzut ≈ Q_const·tau_valve). Koszt: wiele przełączeń zaworu na cykl.
- Powyżej f_track = Q_const/(2π·A_V) zawór przełącza się tylko w szczytach (2 razy na cykl),
  objętość ma kształt trójkąta, amplituda ≈ Q_const/(4f) (minus straty od tau_valve).
- Nowa metryka: liczba przełączeń zaworu na cykl ogona (zmiany znaku s).
- Zawór przelewowy zostaje jako osobne zabezpieczenie.
- Nazewnictwo: "pompa nasyca się" → "zawór przełącza tylko w szczytach / koniec śledzenia".
