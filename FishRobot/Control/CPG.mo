within FishRobot.Control;
block CPG "Generator rytmu machania: u = A·sin(2π·f·t) + bias, z rampą startową i nasyceniem"
  extends Modelica.Blocks.Interfaces.SO;
  parameter Real A = 0.8 "Amplituda komendy pompy";
  parameter Modelica.Units.SI.Frequency f = 1.5 "Częstotliwość machania";
  parameter Real bias = 0 "Przesunięcie (skręt: ogon wychylony na jedną stronę)";
  parameter Real n_ramp = 2 "Czas narastania amplitudy w okresach machania";
  parameter Modelica.Units.SI.Time T_ramp = n_ramp/f "Czas łagodnego narastania amplitudy";
  parameter Real u_max = 1 "Nasycenie komendy";
  Real ramp "Współczynnik narastania 0 -> 1";
  Real u_raw "Komenda przed nasyceniem";
protected
  Real x = time/T_ramp;
equation
  // Gładki start 3x² - 2x³ (pochodna = 0 na obu końcach): bez szarpnięcia prądu przy włączeniu.
  ramp = if x < 1 then x^2*(3 - 2*x) else 1;
  u_raw = ramp*(A*sin(2*Modelica.Constants.pi*f*time) + bias);
  y = noEvent(max(-u_max, min(u_max, u_raw)));
  annotation (
    Icon(graphics={
      Line(points={{-80,0},{-60,40},{-40,0},{-20,-40},{0,0},{20,40},{40,0},{60,-40},{80,0}},
        color={0,0,127}, smooth=Smooth.Bezier),
      Text(extent={{-80,-50},{80,-90}}, textString="f=%f", textColor={0,0,0})}),
    Documentation(info="<html>
<p>Najprostszy generator rytmu (CPG – <i>central pattern generator</i>): sinus o zadanej amplitudzie
i częstotliwości. <code>bias &ne; 0</code> przesuwa średnie położenie ogona, co w prawdziwej rybie
daje skręt.</p>
<p>Rampa startowa <code>3x<sup>2</sup> - 2x<sup>3</sup></code> łagodnie zwiększa amplitudę w czasie
<code>T_ramp</code> (domyślnie 2 okresy machania). Ma dwa zadania:</p>
<ul>
<li>bez niej silnik dostałby skok napięcia i duży prąd rozruchowy,</li>
<li><b>pompa jest integratorem</b>: objętość w komorze to całka z przepływu. Całka z <code>sin(&omega;t)</code>
włączonego w <code>t = 0</code> to <code>(1 - cos &omega;t)/&omega;</code> – przebieg <b>z niezerową średnią</b>.
Ogon machałby wtedy wokół wychylonego położenia, a przesunięcie znikałoby tylko powoli, przez przeciek pompy.
Rampa trwająca kilka okresów prawie usuwa to przesunięcie. Ten sam efekt znasz z silnika krokowego
albo z całkowania sygnału w akcelerometrze.</li>
</ul>
<p>Prawdziwe CPG to sprzężone oscylatory nieliniowe (np. Matsuoka, Hopf), które płynnie zmieniają
częstotliwość i fazę. Do badania pasma układu wystarczy sinus.</p>
</html>"));
end CPG;
