within FishRobot.Control;
block DepthPID "Regulator głębokości kaskadowy: PID głębokości -> zadana objętość pęcherza -> P położenia tłoka"
  parameter Modelica.Units.SI.Volume V_max = 12.5e-6 "Maksymalna objętość pęcherza (ze strzykawki)";
  parameter Real margin = 0.05 "Zapas od ograniczników jako ułamek V_max";
  parameter Modelica.Units.SI.Volume V_ff = 6e-6
    "Punkt pracy: szacowana objętość neutralna, wartość startowa całki (nie musi być dokładna – resztę zrobi całka)";
  parameter Real k_z(unit="m3/m") = 2e-5 "Wzmocnienie: zmiana objętości pęcherza na metr błędu głębokości";
  parameter Modelica.Units.SI.Time Ti = 120 "Czas zdwojenia (całkowanie)";
  parameter Modelica.Units.SI.Time Td = 3 "Czas wyprzedzenia (różniczkowanie)";
  parameter Real K_V(unit="1/m3") = 1e6 "Wzmocnienie pętli wewnętrznej: komenda silnika na m3 błędu objętości";
  parameter Modelica.Units.SI.Velocity v_ref_max = 0.03
    "Maksymalna prędkość zmian zadanej głębokości (filtr zadanej)";

  Modelica.Blocks.Interfaces.RealInput z_ref(unit="m") "Zadana głębokość (z < 0 pod wodą)"
    annotation (Placement(transformation(extent={{-140,40},{-100,80}})));
  Modelica.Blocks.Interfaces.RealInput z(unit="m") "Zmierzona głębokość (czujnik ciśnienia)"
    annotation (Placement(transformation(extent={{-140,-20},{-100,20}})));
  Modelica.Blocks.Interfaces.RealInput V_b(unit="m3") "Zmierzona objętość pęcherza (enkoder tłoka)"
    annotation (Placement(transformation(extent={{-140,-80},{-100,-40}})));
  Modelica.Blocks.Interfaces.RealOutput u "Komenda mostka H silnika strzykawki"
    annotation (Placement(transformation(extent={{100,-10},{120,10}})));
  Modelica.Blocks.Interfaces.RealOutput V_ref(unit="m3") "Zadana objętość pęcherza (wyjście pętli zewnętrznej)"
    annotation (Placement(transformation(extent={{100,50},{120,70}})));

  Modelica.Blocks.Continuous.LimPID depthLoop(
    controllerType=Modelica.Blocks.Types.SimpleController.PID,
    k=k_z, Ti=Ti, Td=Td, Nd=10, Ni=0.9,
    yMax=(1 - margin)*V_max, yMin=margin*V_max,
    initType=Modelica.Blocks.Types.Init.InitialOutput, y_start=V_ff)
    "Pętla zewnętrzna: głębokość -> zadana objętość pęcherza (z anti-windup)"
    annotation (Placement(transformation(extent={{-40,50},{-20,70}})));
  Modelica.Blocks.Nonlinear.SlewRateLimiter refLimiter(Rising=v_ref_max, Falling=-v_ref_max, Td=0.1, strict=true)
    "Filtr zadanej: skok głębokości zamieniony na rampę"
    annotation (Placement(transformation(extent={{-80,50},{-60,70}})));
  Modelica.Blocks.Nonlinear.Limiter saturation(uMax=1, uMin=-1, strict=true) "Nasycenie komendy mostka"
    annotation (Placement(transformation(extent={{60,-10},{80,10}})));
equation
  connect(z_ref, refLimiter.u) annotation (Line(points={{-120,60},{-82,60}}, color={0,0,127}));
  connect(refLimiter.y, depthLoop.u_s) annotation (Line(points={{-59,60},{-42,60}}, color={0,0,127}));
  connect(z, depthLoop.u_m) annotation (Line(points={{-120,0},{-30,0},{-30,48}}, color={0,0,127}));
  connect(depthLoop.y, V_ref) annotation (Line(points={{-19,60},{110,60}}, color={0,0,127}));
  // Pętla wewnętrzna P: silnik kręci, dopóki objętość nie dojdzie do zadanej.
  saturation.u = K_V*(V_ref - V_b);
  connect(saturation.y, u) annotation (Line(points={{81,0},{110,0}}, color={0,0,127}));
  annotation (
    Icon(graphics={
      Rectangle(extent={{-100,100},{100,-100}}, lineColor={0,0,127}, fillColor={255,255,255},
        fillPattern=FillPattern.Solid),
      Text(extent={{-90,40},{90,-40}}, textString="PID z", textColor={0,0,127})}),
    Documentation(info="<html>
<p><b>Dlaczego kaskada, a nie jeden PID „z_ref &rarr; silnik”:</b> od komendy silnika do głębokości są trzy całkowania:
prędkość tłoka &rarr; objętość pęcherza &rarr; (siła &rarr;) prędkość &rarr; głębokość. Jeden PID na takim obiekcie jest
trudny do nastrojenia i łatwo wpada w oscylacje. Dzielimy problem na dwie pętle:</p>
<ol>
<li><b>Wewnętrzna (szybka, P):</b> <code>u = K_V·(V_ref - V_b)</code>. Silnik kręci tłokiem, aż objętość pęcherza dojdzie
do zadanej. Przy <code>K_V = 1e6</code> błąd 1 ml daje pełną komendę. Czas reakcji: kilka sekund.</li>
<li><b>Zewnętrzna (wolna, PID):</b> <code>LimPID</code> z <code>Modelica.Blocks.Continuous</code> zamienia błąd głębokości na
zadaną objętość pęcherza:
<pre>  V_ref = k_z·(e + (1/Ti)&int;e dt + Td·de/dt),   e = z_ref - z</pre>
Punkt pracy <code>V_ff</code> (szacowana objętość neutralna) to wartość startowa całki.</li>
</ol>
<p><b>Filtr zadanej</b> (<code>SlewRateLimiter</code>): skok zadanej głębokości zamieniamy na rampę
<code>v_ref_max</code> (3 cm/s – mniej więcej tyle, ile ryba i tak osiąga). Bez filtra błąd przez pierwsze
kilkadziesiąt sekund jest duży, całka „nabiera” wartości i ryba przelatuje za cel.</p>
<p><b>Inicjalizacja</b> <code>InitialOutput</code> z <code>y_start = V_ff</code>: na starcie błąd jest zerowy, człon D
startuje w stanie ustalonym, a całka przejmuje cały punkt pracy. Uwaga na pułapkę w MSL: przy włączonym wejściu
<code>u_ff</code> warunek <code>y_start</code> dotyczy wyjścia PID <i>bez</i> sprzężenia w przód, a jednocześnie musi
mieścić się w <code>[yMin, yMax]</code>; dlatego punkt pracy podajemy przez całkę, a nie przez <code>u_ff</code>.
Przy <code>InitialState</code> stan członu różniczkującego startowałby od zera, a pomiar od -0,5 m,
co dałoby w chwili 0 sztuczną „pochodną” i skok zadanej objętości do maksimum.</p>
<p>Parametry <code>LimPID</code>:</p>
<ul>
<li><code>k = k_z</code> – 20 ml na metr błędu, czyli 2 ml na 10 cm: przy błędzie 10 cm ryba ma ok. 0,02 N nadmiaru wyporu,</li>
<li><code>Td = 3 s</code> – człon różniczkujący daje tłumienie. Działa tylko na pomiar (<code>wd = 0</code>), więc skok
zadanej głębokości nie powoduje „kopnięcia” komendy. <code>Nd = 10</code> filtruje różniczkowanie,</li>
<li><code>Ti = 120 s</code> – całka usuwa błąd ustalony, gdy <code>V_ff</code> nie jest dokładnie objętością neutralną
(a nigdy nie jest: masa ryby, temperatura wody, ściśliwość),</li>
<li><code>yMin, yMax</code> – zadana objętość mieści się w skoku tłoka z 5% zapasem od ograniczników,</li>
<li><b>anti-windup</b> (<code>Ni = 0,9</code>): gdy wyjście jest nasycone, całka jest „odciągana” sygnałem
<code>(y - y_przed_nasyceniem)/(Ni·Ti)</code>, więc nie nabiera ogromnej wartości podczas długiego zanurzania
i nie powoduje dużego przeregulowania po wyjściu z nasycenia.</li>
</ul>
<p><b>Strojenie:</b> obiekt w pobliżu równowagi to masa <code>m + m_added</code> sterowana siłą
<code>&rho;·g·&Delta;V</code>. Człon P daje „sprężynę” <code>&rho;·g·k_z &asymp; 0,2 N/m</code> (okres drgań ok. 17 s),
a człon D „tłumik” <code>&rho;·g·k_z·Td &asymp; 0,6 N·s/m</code> (tłumienie ok. 0,55; resztę dokłada opór wody).
Wartości wybrano przeglądem parametrów (k_z, Ti, Td) na scenariuszu <code>DepthControl</code>: przeregulowanie
ok. 6%, błąd końcowy &lt; 1 cm. Zbyt duże <code>Td</code> przy dużym <code>k_z</code> daje drgania: filtr różniczkowania
i pętla wewnętrzna dokładają opóźnienie, którego prosty rachunek nie uwzględnia.</p>
</html>"));
end DepthPID;
