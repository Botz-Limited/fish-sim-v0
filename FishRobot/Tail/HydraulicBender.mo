within FishRobot.Tail;
model HydraulicBender "Przetwornik hydrauliczno-obrotowy: różnica ciśnień komór -> moment na ogonie"
  parameter Real D_tail(unit="m3/rad") = 2e-5
    "Objętość wypierana na radian kąta ogona, = A_eff·r_eff (PLACEHOLDER – do identyfikacji)";

  FishRobot.Interfaces.HydraulicPort_a port_L "Strona komory L"
    annotation (Placement(transformation(extent={{-110,30},{-90,50}})));
  FishRobot.Interfaces.HydraulicPort_a port_R "Strona komory R"
    annotation (Placement(transformation(extent={{-110,-50},{-90,-30}})));
  Modelica.Mechanics.Rotational.Interfaces.Flange_b flange "Oś ogona"
    annotation (Placement(transformation(extent={{90,-10},{110,10}})));

  Modelica.Units.SI.Angle phi "Kąt ogona";
  Modelica.Units.SI.AngularVelocity w "Prędkość kątowa ogona";
  Modelica.Units.SI.Torque tau_hyd "Moment od ciśnienia: D_tail·(p_L - p_R)";
  Modelica.Units.SI.Power P_hyd "Moc hydrauliczna zamieniana na mechaniczną";
equation
  phi = flange.phi;
  w = der(phi);
  // Kinematyka: obrót ogona o dθ wypycha D_tail·dθ cieczy z jednej strony i zasysa po drugiej.
  port_L.V_flow = D_tail*w;
  port_R.V_flow = -D_tail*w;
  // Statyka (zasada prac przygotowanych): ta sama stała D_tail łączy ciśnienie z momentem.
  tau_hyd = D_tail*(port_L.p - port_R.p);
  flange.tau = -tau_hyd;
  P_hyd = tau_hyd*w;
  annotation (
    Icon(graphics={
      Rectangle(extent={{-80,70},{40,-70}}, lineColor={0,0,0}, fillColor={255,255,255},
        fillPattern=FillPattern.Solid),
      Rectangle(extent={{-80,70},{40,5}}, lineColor={0,128,255}, fillColor={170,213,255},
        fillPattern=FillPattern.Solid),
      Rectangle(extent={{-80,-5},{40,-70}}, lineColor={0,128,255}, fillColor={170,213,255},
        fillPattern=FillPattern.Solid),
      Polygon(points={{-60,5},{-60,-5},{40,0},{-60,5}}, lineColor={0,0,0}, fillColor={95,95,95},
        fillPattern=FillPattern.Solid),
      Line(points={{40,0},{90,0}}),
      Text(extent={{-150,120},{150,80}}, textString="%name", textColor={0,0,255})}),
    Documentation(info="<html>
<p>Idealny „tłok obrotowy”: odpowiednik transformatora między dziedziną hydrauliczną i obrotową
(tak jak <code>RotationalEMF</code> między elektryczną i obrotową).</p>
<pre>  Q_L = D_tail·d&theta;/dt,   Q_R = -D_tail·d&theta;/dt
  &tau;   = D_tail·(p_L - p_R)</pre>
<p>Ta sama stała <code>D_tail = A_eff·r_eff</code> w obu równaniach gwarantuje
<b>spójność energetyczną</b>: moc hydrauliczna <code>p_L·Q_L + p_R·Q_R = (p_L - p_R)·D_tail·&omega;</code>
jest dokładnie równa mocy mechanicznej <code>&tau;·&omega;</code>. Przetwornik nie tworzy ani nie traci energii.</p>
<p><b>Dlaczego to sformułowanie, a nie „&theta; z różnicy objętości komór przez sztywność”:</b> drugi wariant
zakłada, że kąt ogona jest algebraiczną funkcją objętości, czyli pomija bezwładność ogona i nie daje momentu,
który można przekazać do innego symulatora (np. MuJoCo). Tutaj ogon ma własną dynamikę, a komora może
jednocześnie pęcznieć (krzywa p–V w <code>Chamber</code> = podatność przy zablokowanym ogonie)
i przesuwać ogon (<code>D_tail</code>). Całkowita objętość po stronie L to <code>V_L + D_tail·&theta;</code>.</p>
<p><code>D_tail</code> można zmierzyć statycznie: przy wolnym ogonie zmierz objętość wtłoczoną i kąt,
odejmij objętość z krzywej p–V przy zablokowanym ogonie.</p>
</html>"));
end HydraulicBender;
