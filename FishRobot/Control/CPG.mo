within FishRobot.Control;
block CPG "Generator rytmu machania: V_ref = A_V·sin(2π·f·t) + bias_V z rampą, regulator przekaźnikowy z histerezą i minimalnym czasem stanu zaworów"
  extends Modelica.Blocks.Interfaces.SO;
  import Modelica.Units.SI;
  parameter SI.Volume A_V = 4e-6 "Amplituda zadanej objętości przetłoczonej (PLACEHOLDER)";
  parameter SI.Frequency f = 1.5 "Zadana częstotliwość machania (ograniczana do [tail_freq_min, tail_freq_max])";
  parameter SI.Volume bias_V = 0 "Przesunięcie zadanej objętości (skręt: ogon wychylony na jedną stronę)";
  parameter Real n_ramp = 2 "Czas narastania amplitudy w okresach machania";
  parameter SI.Volume delta = 1e-6 "Histereza regulatora przekaźnikowego δ (PLACEHOLDER)";
  parameter SI.Time valve_min_dwell = 0.2
    "Minimalny czas między przełączeniami zaworów: zawór przełącza się najwyżej ~5 razy/s (PLACEHOLDER)";
  parameter SI.Frequency tail_freq_min = 1.5
    "Najniższa dozwolona częstotliwość (decyzja: 1,5 Hz we wszystkich modelach; tuż nad f_track = Q_const/(2π·A_V) ≈ 1,41 Hz)";
  parameter SI.Frequency tail_freq_max = 2.5
    "Najwyższa dozwolona częstotliwość = 1/(2·valve_min_dwell): 2 przełączenia na cykl, każdy stan ≥ valve_min_dwell";
  final parameter SI.Frequency f_eff = min(max(f, tail_freq_min), tail_freq_max)
    "Częstotliwość faktycznie użyta (f ograniczone do [tail_freq_min, tail_freq_max])";
  parameter SI.Time T_ramp = n_ramp/f_eff "Czas łagodnego narastania amplitudy";
  parameter Boolean enable = true "= false: pompa wyłączona (y = 0)";

  Modelica.Blocks.Interfaces.RealInput V_p(unit="m3") "Zmierzona objętość przetłoczona (TailDrive.V_p)"
    annotation (Placement(transformation(extent={{-140,-20},{-100,20}})));

  Real ramp "Współczynnik narastania 0 -> 1";
  SI.Volume V_ref "Zadana objętość przetłoczona R -> L";
  SI.Volume e = V_ref - V_p "Uchyb regulacji";
  Boolean up(start=true, fixed=true) "Stan przekaźnika: true = s = +1 (R -> L), false = s = -1 (L -> R)";
  discrete SI.Time t_switch(start=-1e3, fixed=true) "Czas ostatniego przełączenia zaworów";
  Real s = if up then 1 else -1 "Kierunek zaworów ±1";
protected
  Real x = time/T_ramp;
  Boolean ready = time - pre(t_switch) >= valve_min_dwell "Minął minimalny czas stanu zaworu";
initial equation
  assert(tail_freq_max <= 1/(2*valve_min_dwell) + 1e-9,
    "CPG: tail_freq_max > 1/(2·valve_min_dwell) – zawór nie zdąży przełączyć się 2 razy na cykl");
  assert(tail_freq_min <= tail_freq_max, "CPG: tail_freq_min > tail_freq_max");
  assert(f >= tail_freq_min and f <= tail_freq_max,
    "CPG: f poza zakresem [tail_freq_min, tail_freq_max] – użyto f_eff = " + String(f_eff) + " Hz",
    AssertionLevel.warning);
equation
  // Gładki start 3x² - 2x³: zadana objętość rośnie od zera, więc ogon nie startuje z wychyleniem.
  ramp = if x < 1 then x^2*(3 - 2*x) else 1;
  V_ref = ramp*(A_V*sin(2*Modelica.Constants.pi*f_eff*time) + bias_V);
  // Przekaźnik z histerezą i minimalnym czasem stanu: przełącza dopiero, gdy uchyb wyjdzie poza ±δ
  // w stronę przeciwną do bieżącego stanu ORAZ od ostatniego przełączenia minęło valve_min_dwell.
  // Jeśli uchyb przekroczy próg w trakcie blokady, przełączenie następuje w chwili jej końca.
  // Po przełączeniu warunek od razu staje się fałszywy (nowy stan, ready = false) – brak pętli zdarzeń.
  when ready and (if pre(up) then e < -delta else e > delta) then
    up = not pre(up);
    t_switch = time;
  end when;
  y = if enable then s else 0;
  annotation (
    Icon(graphics={
      Line(points={{-80,0},{-60,40},{-40,0},{-20,-40},{0,0},{20,40},{40,0},{60,-40},{80,0}},
        color={0,0,127}, smooth=Smooth.Bezier),
      Line(points={{-30,-60},{-10,-60},{-10,-80},{30,-80}}, color={0,0,0}),
      Line(points={{-30,-80},{10,-80},{10,-60},{30,-60}}, color={0,0,0}),
      Text(extent={{-80,90},{80,50}}, textString="f=%f", textColor={0,0,0})}),
    Documentation(info="<html>
<p>Generator rytmu (CPG – <i>central pattern generator</i>) dla napędu o stałym wydatku. Pompa kręci się zawsze
z tą samą prędkością, więc nie da się nią płynnie dozować przepływu – sterujemy wyłącznie kierunkiem
zaworów <code>s = &plusmn;1</code>. Zadana jest objętość przetłoczona z gałęzi R do L:</p>
<pre>  V_ref = ramp(t)·(A_V·sin(2&pi;f_eff·t) + bias_V)
  e = V_ref - V_p
  jeśli time - t_switch &lt; valve_min_dwell:  s bez zmian
  e &gt;  &delta;  &rArr;  s = +1   (R &rarr; L)
  e &lt; -&delta;  &rArr;  s = -1   (L &rarr; R)
  w przeciwnym razie s bez zmian (start: s = +1)</pre>
<p><b>Ograniczenie zaworu:</b> zawór przełącza się najwyżej ok. 5 razy/s, więc każdy stan trwa co najmniej
<code>valve_min_dwell = 0,2 s</code> (<code>t_switch</code> – czas ostatniego przełączenia). Jeśli uchyb przekroczy
&plusmn;&delta; w trakcie blokady, zawór przełącza się w chwili jej końca.</p>
<p><b>Zakres częstotliwości</b> <code>[tail_freq_min, tail_freq_max] = [1,5; 2,5] Hz</code>; <code>f</code> spoza zakresu
jest przycinane do <code>f_eff</code> (z ostrzeżeniem):</p>
<ul>
<li><code>tail_freq_max = 1/(2·valve_min_dwell)</code>: 2 przełączenia na cykl, każdy stan &ge; 0,2 s.</li>
<li><code>tail_freq_min = 1,5 Hz</code> (decyzja projektowa) leży tuż nad <code>f_track = Q_const/(2&pi;·A_V) &asymp; 1,41 Hz</code> (A_V = 4 ml,
<code>Q_const &asymp; 35 ml/s</code>). Poniżej <code>f_track</code> pompa jest szybsza niż zadana zmiana objętości
i regulator musiałby „piłować” wokół <code>V_ref</code> wiele razy na cykl – zawór tego nie zrobi, a każde
przełączenie szarpie ogonem.</li>
<li>W zakresie zawór przełącza się tylko w szczytach (2 razy na cykl), objętość ma kształt trójkąta o amplitudzie
ok. <code>Q_const/(4f)</code> (minus straty od <code>tau_valve</code>) – wyższa częstotliwość = mniejszy ruch.</li>
</ul>
<p>Rampa startowa <code>3x<sup>2</sup> - 2x<sup>3</sup></code> przez <code>n_ramp</code> okresów zostaje: pompa jest
integratorem, a zadany sinus włączony skokowo dałby przesunięcie średniego położenia ogona.</p>
<p><code>bias_V &ne; 0</code> przesuwa średnie położenie ogona (skręt). <code>enable = false</code> daje <code>y = 0</code>,
czyli pompa stoi (to jedyne znaczenie zera – zawory nie mają położenia zamkniętego).</p>
</html>"));
end CPG;
