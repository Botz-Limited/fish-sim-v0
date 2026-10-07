within FishRobot.Calibration;
model VerticalStep "Stanowisko: skok objętości pęcherza z pływalności neutralnej, ryba się wynurza (krok 11)"
  extends Modelica.Icons.Example;

  parameter Modelica.Units.SI.Volume dV = 1e-6 "Skok objętości pęcherza (z położenia tłoka)";
  parameter Modelica.Units.SI.Time t_step = 2 "Chwila skoku";
  parameter Modelica.Units.SI.Position z_start = -1.5 "Głębokość startowa (ryba zawieszona neutralnie)";

  FishRobot.Buoyancy.VerticalDynamics fish(z_start=z_start, useCompressibility=true)
    annotation (Placement(transformation(extent={{-10,-10},{10,10}})));
  // Pęcherz neutralny na głębokości startowej: trzeba dołożyć tyle, ile ścisnęło się powietrze w kadłubie.
  parameter Modelica.Units.SI.Volume V_b0 = fish.V_b_neutral + fish.V_air0
    - fish.V_air0*fish.p_atm/(fish.p_atm + fish.rho*Modelica.Constants.g_n*(-z_start))
    "Pęcherz neutralny na głębokości z_start";
  Modelica.Blocks.Sources.Step bladder(height=dV, offset=V_b0, startTime=t_step)
    "Pęcherz: neutralny, potem większy o dV"
    annotation (Placement(transformation(extent={{-60,-10},{-40,10}})));

  Modelica.Units.SI.Position z = fish.z "Położenie (czujnik ciśnienia w kadłubie)";
equation
  connect(bladder.y, fish.V_b) annotation (Line(points={{-39,0},{-12,0}}, color={0,0,127}));
  annotation (
    experiment(StopTime=20, Interval=0.01, Tolerance=1e-8),
    Documentation(info="<html>
<p>Ryba zawieszona neutralnie na głębokości <code>z_start</code>, potem strzykawka skokowo powiększa pęcherz
o <code>dV</code>. Siła wyporu rośnie o znane <code>&rho;·g·dV</code>, a ryba rozpędza się w górę do prędkości granicznej:</p>
<pre>  (m + m_added_z)·v' = &rho;·g·dV - &frac12;·&rho;·C_dz·A_z·v·|v|</pre>
<p>Kadłub ma kieszeń powietrza (<code>V_air0</code> z ważenia na głębokościach), która przy wynurzaniu
się rozpręża: na 0,5 m drogi z 1,5 m to ok. 0,7 ml dodatkowego wyporu, czyli tyle co sam skok pęcherza.
Dlatego <code>useCompressibility = true</code>, a pęcherz startowy jest neutralny na głębokości <code>z_start</code>.</p>
<p>Prędkość graniczna zależy tylko od oporu, a czas rozpędzania od masy z masą dodaną. Wymuszenie jest znane,
więc jeden przebieg z(t) wyznacza oba parametry, inaczej niż wybieg kadłuba (krok 10), w którym siła jest nieznana.</p>
</html>"));
end VerticalStep;
