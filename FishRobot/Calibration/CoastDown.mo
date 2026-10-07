within FishRobot.Calibration;
model CoastDown "Stanowisko: wybieg kadłuba po puszczeniu z prędkością U_start, napęd wyłączony (krok 10)"
  extends Modelica.Icons.Example;

  FishRobot.Propulsion.SurgeDynamics surge(U_start=0.15)
    annotation (Placement(transformation(extent={{-10,-10},{10,10}})));
  Modelica.Blocks.Sources.Constant noThrust(k=0) "Ogon nieruchomy"
    annotation (Placement(transformation(extent={{-60,-10},{-40,10}})));

  Modelica.Units.SI.Position x = surge.x "Położenie (kamera nad basenem)";
  Modelica.Units.SI.Velocity U = surge.U "Prędkość";
equation
  connect(noThrust.y, surge.T) annotation (Line(points={{-39,0},{-12,0}}, color={0,0,127}));
  annotation (
    experiment(StopTime=20, Interval=0.01, Tolerance=1e-8),
    Documentation(info="<html>
<p>Ryba rozpędzona (np. wózkiem holowniczym) i puszczona z prędkością <code>U_start</code>, ogon nieruchomy.
Kamera nad basenem rejestruje położenie <code>x(t)</code>. Bez ciągu:</p>
<pre>  (m + m_added_x)·U' = -k_d·U²,   k_d = &frac12;·&rho;·C_d·A
  x(t) = (M/k_d)·ln(1 + k_d·U_start·t/M),   M = m + m_added_x</pre>
<p>Przebieg zależy tylko od <code>k_d/M</code>, więc <code>C_d</code> musi pochodzić z holowania ze stałą prędkością,
a <code>m</code> z ważenia. Dopiero wtedy wybieg daje masę dodaną <code>m_added_x = M - m</code>.</p>
</html>"));
end CoastDown;
