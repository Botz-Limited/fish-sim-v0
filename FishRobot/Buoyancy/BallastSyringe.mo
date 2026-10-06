within FishRobot.Buoyancy;
model BallastSyringe "Strzykawka balastowa: mostek H + silnik DC + przekładnia + śruba pociągowa + tłok z ogranicznikami"
  import Modelica.Constants.pi;
  parameter Modelica.Units.SI.Diameter d_piston = 20e-3 "Średnica tłoka (PLACEHOLDER – do identyfikacji)";
  parameter Modelica.Units.SI.Length x_max = 40e-3 "Skok tłoka (PLACEHOLDER – do identyfikacji)";
  parameter Modelica.Units.SI.Length x_start = 20e-3 "Położenie początkowe tłoka";
  parameter Real gear_ratio = 30 "Przełożenie przekładni silnik -> śruba (PLACEHOLDER – do identyfikacji)";
  parameter Modelica.Units.SI.Length lead = 1e-3 "Skok gwintu śruby na obrót (PLACEHOLDER – do identyfikacji)";
  parameter Modelica.Units.SI.Mass m_piston = 0.02 "Masa tłoka i nakrętki (PLACEHOLDER – do identyfikacji)";
  parameter Modelica.Units.SI.TranslationalSpringConstant c_stop = 1e6 "Sztywność ograniczników";
  parameter Modelica.Units.SI.TranslationalDampingConstant d_stop = 1e3 "Tłumienie ograniczników";
  parameter Modelica.Units.SI.Density rho = 998.2 "Gęstość wody";
  final parameter Modelica.Units.SI.Area A_piston = pi*d_piston^2/4 "Pole tłoka";
  final parameter Modelica.Units.SI.Volume V_max = A_piston*x_max "Maksymalna objętość pęcherza";

  Modelica.Blocks.Interfaces.RealInput u "Komenda mostka H silnika strzykawki, u ∈ [-1, 1]"
    annotation (Placement(transformation(extent={{-140,40},{-100,80}})));
  Modelica.Blocks.Interfaces.RealInput depth(unit="m") "Głębokość (dodatnia pod wodą) – ciśnienie hydrostatyczne na tłoku"
    annotation (Placement(transformation(extent={{-140,-80},{-100,-40}})));
  Modelica.Electrical.Analog.Interfaces.PositivePin bat "Do bieguna + baterii"
    annotation (Placement(transformation(extent={{-110,-10},{-90,10}})));
  Modelica.Electrical.Analog.Interfaces.NegativePin n "Wspólny biegun ujemny"
    annotation (Placement(transformation(extent={{-10,-110},{10,-90}})));
  Modelica.Blocks.Interfaces.RealOutput V_b(unit="m3") "Objętość pęcherza (wypierana przez tłok)"
    annotation (Placement(transformation(extent={{100,-10},{120,10}})));

  Modelica.Units.SI.Position x = piston.s "Położenie tłoka (0 = pęcherz pusty)";
  Modelica.Units.SI.Current i_motor = motor.i "Prąd silnika strzykawki";
  Modelica.Units.SI.Force F_water = A_piston*rho*Modelica.Constants.g_n*noEvent(max(0, depth))
    "Siła ciśnienia hydrostatycznego na tłok";

  FishRobot.Electrical.HBridge bridge
    annotation (Placement(transformation(extent={{-80,-10},{-60,10}})));
  FishRobot.Electrical.DCMotor motor(initRotor=false) "Wał sztywno połączony z tłokiem – warunki początkowe ma tłok"
    annotation (Placement(transformation(extent={{-50,-10},{-30,10}})));
  Modelica.Mechanics.Rotational.Components.IdealGear gear(ratio=gear_ratio)
    annotation (Placement(transformation(extent={{-20,-10},{0,10}})));
  Modelica.Mechanics.Translational.Components.IdealGearR2T screw(ratio=2*pi/lead) "Śruba pociągowa [rad/m]"
    annotation (Placement(transformation(extent={{10,-10},{30,10}})));
  Modelica.Mechanics.Translational.Components.Mass piston(m=m_piston,
    s(start=x_start, fixed=true), v(start=0, fixed=true))
    annotation (Placement(transformation(extent={{40,-10},{60,10}})));
  Modelica.Mechanics.Translational.Components.ElastoGap stopLow(c=c_stop, d=d_stop, s_rel0=0)
    "Ogranicznik dolny x = 0"
    annotation (Placement(transformation(extent={{40,-50},{60,-30}})));
  Modelica.Mechanics.Translational.Components.Fixed fixedLow(s0=0)
    annotation (Placement(transformation(extent={{10,-50},{30,-30}})));
  Modelica.Mechanics.Translational.Components.ElastoGap stopHigh(c=c_stop, d=d_stop, s_rel0=0)
    "Ogranicznik górny x = x_max"
    annotation (Placement(transformation(extent={{70,-50},{90,-30}})));
  Modelica.Mechanics.Translational.Components.Fixed fixedHigh(s0=x_max)
    annotation (Placement(transformation(extent={{90,-80},{110,-60}})));
  Modelica.Mechanics.Translational.Sources.Force waterLoad "Ciśnienie wody wpycha tłok"
    annotation (Placement(transformation(extent={{90,20},{70,40}})));
equation
  connect(u, bridge.u) annotation (Line(points={{-120,60},{-70,60},{-70,12}}, color={0,0,127}));
  connect(bat, bridge.bat) annotation (Line(points={{-100,0},{-90,0},{-90,4},{-80,4}}, color={0,0,255}));
  connect(bridge.n, n) annotation (Line(points={{-70,-10},{-70,-100},{0,-100}}, color={0,0,255}));
  connect(bridge.mot, motor.p) annotation (Line(points={{-60,4},{-50,4}}, color={0,0,255}));
  connect(motor.n, n) annotation (Line(points={{-50,-4},{-56,-4},{-56,-100},{0,-100}}, color={0,0,255}));
  connect(motor.flange, gear.flange_a) annotation (Line(points={{-30,0},{-20,0}}));
  connect(gear.flange_b, screw.flangeR) annotation (Line(points={{0,0},{10,0}}));
  connect(screw.flangeT, piston.flange_a) annotation (Line(points={{30,0},{40,0}}, color={0,127,0}));
  connect(fixedLow.flange, stopLow.flange_a) annotation (Line(points={{20,-40},{40,-40}}, color={0,127,0}));
  connect(stopLow.flange_b, piston.flange_b) annotation (Line(points={{60,-40},{64,-40},{64,0},{60,0}}, color={0,127,0}));
  connect(piston.flange_b, stopHigh.flange_a) annotation (Line(points={{60,0},{66,0},{66,-40},{70,-40}}, color={0,127,0}));
  connect(stopHigh.flange_b, fixedHigh.flange) annotation (Line(points={{90,-40},{100,-40},{100,-70}}, color={0,127,0}));
  connect(waterLoad.flange, piston.flange_b) annotation (Line(points={{70,30},{64,30},{64,0},{60,0}}, color={0,127,0}));
  waterLoad.f = -F_water;
  V_b = A_piston*piston.s;
  annotation (
    Icon(graphics={
      Rectangle(extent={{-60,40},{80,-40}}, lineColor={0,0,0}, fillColor={255,255,255},
        fillPattern=FillPattern.Solid),
      Rectangle(extent={{0,40},{80,-40}}, lineColor={0,0,0}, fillColor={170,213,255},
        fillPattern=FillPattern.Solid),
      Rectangle(extent={{-10,40},{0,-40}}, lineColor={0,0,0}, fillColor={95,95,95},
        fillPattern=FillPattern.Solid),
      Line(points={{-90,0},{-10,0}}, thickness=1),
      Text(extent={{-150,100},{150,60}}, textString="%name", textColor={0,0,255})}),
    Documentation(info="<html>
<p>Strzykawka zmienia objętość wypieraną przez rybę, a więc jej wyporność. Łańcuch napędowy:</p>
<pre>  mostek H &rarr; silnik DC &rarr; przekładnia (gear_ratio) &rarr; śruba pociągowa (skok lead) &rarr; tłok
  V_b = A_tłoka·x</pre>
<p><b>Śruba pociągowa</b> (<code>IdealGearR2T</code>, przełożenie <code>2&pi;/lead</code> rad/m) zamienia obrót na przesuw.
Przy skoku 1 mm i przekładni 30:1 obrót silnika o 30 obrotów przesuwa tłok o 1 mm – mała prędkość, ale ogromna siła.
Prawdziwa śruba trapezowa jest samohamowna (ciśnienie wody nie cofnie tłoka przy wyłączonym silniku); tutaj
śruba jest idealna, więc tłok trzyma pozycję tylko dzięki regulatorowi. Uproszczenie do zastąpienia przez
<code>LossyGear</code>, jeśli będzie potrzebne.</p>
<p><b>Ograniczniki</b> (<code>ElastoGap</code>) to sztywne sprężyny z tłumieniem, które działają tylko przy kontakcie:
na <code>x = 0</code> i <code>x = x_max</code>. Regulator głębokości ogranicza zadaną objętość do zakresu ze zapasem,
więc w normalnej pracy tłok ich nie dotyka.</p>
<p><b>Obciążenie:</b> ciśnienie hydrostatyczne <code>&rho;·g·głębokość</code> działa na tłok i wpycha go do środka,
więc na większej głębokości silnik musi pchać mocniej, żeby powiększyć pęcherz.</p>
</html>"));
end BallastSyringe;
