within FishRobot.Electrical;
model DCMotor "Silnik DC z magnesami trwałymi: R–L + RotationalEMF + inercja wirnika + tarcie lepkie"
  parameter Modelica.Units.SI.Resistance R = 1.0 "Rezystancja uzwojenia (PLACEHOLDER – do identyfikacji)";
  parameter Modelica.Units.SI.Inductance L = 5e-4 "Indukcyjność uzwojenia (PLACEHOLDER – do identyfikacji)";
  parameter Modelica.Units.SI.ElectricalTorqueConstant k = 0.01
    "Stała momentu = stała napięciowa [N·m/A = V·s/rad] (PLACEHOLDER – do identyfikacji)";
  parameter Modelica.Units.SI.Inertia J = 5e-6 "Moment bezwładności wirnika (PLACEHOLDER – do identyfikacji)";
  parameter Modelica.Units.SI.RotationalDampingConstant b = 1e-6
    "Tarcie lepkie w łożyskach (PLACEHOLDER – do identyfikacji)";
  parameter Boolean initRotor = true
    "= true: wirnik startuje z phi = 0, w = 0. Ustaw false, gdy wał jest sztywno połączony z elementem, który ma już własne warunki początkowe (np. tłok przez przekładnię)"
    annotation (Evaluate=true, choices(checkBox=true));

  Modelica.Electrical.Analog.Interfaces.PositivePin p
    annotation (Placement(transformation(extent={{-110,30},{-90,50}})));
  Modelica.Electrical.Analog.Interfaces.NegativePin n
    annotation (Placement(transformation(extent={{-110,-50},{-90,-30}})));
  Modelica.Mechanics.Rotational.Interfaces.Flange_b flange "Wał silnika"
    annotation (Placement(transformation(extent={{90,-10},{110,10}})));

  Modelica.Units.SI.Current i = inductor.i "Prąd silnika";
  Modelica.Units.SI.AngularVelocity w = rotor.w "Prędkość obrotowa wału";
  Modelica.Units.SI.Power P_el = (p.v - n.v)*p.i "Moc elektryczna pobierana";
  Modelica.Units.SI.Power P_cu = resistor.LossPower "Straty w miedzi R·i²";
  Modelica.Units.SI.Power P_fric = friction.lossPower "Straty tarcia w łożyskach";

  Modelica.Electrical.Analog.Basic.Resistor resistor(R=R)
    annotation (Placement(transformation(extent={{-80,30},{-60,50}})));
  Modelica.Electrical.Analog.Basic.Inductor inductor(L=L, i(start=0, fixed=true))
    annotation (Placement(transformation(extent={{-40,30},{-20,50}})));
  Modelica.Electrical.Analog.Basic.RotationalEMF emf(k=k)
    annotation (Placement(transformation(extent={{-10,-10},{10,10}})));
  Modelica.Mechanics.Rotational.Components.Inertia rotor(J=J,
    phi(start=0, fixed=initRotor), w(start=0, fixed=initRotor))
    annotation (Placement(transformation(extent={{30,-10},{50,10}})));
  Modelica.Mechanics.Rotational.Components.Damper friction(d=b)
    annotation (Placement(transformation(extent={{-10,-10},{10,10}}, rotation=-90, origin={70,-30})));
  Modelica.Mechanics.Rotational.Components.Fixed housing "Obudowa (moment reakcji idzie w kadłub)"
    annotation (Placement(transformation(extent={{60,-70},{80,-50}})));
equation
  connect(p, resistor.p) annotation (Line(points={{-100,40},{-80,40}}, color={0,0,255}));
  connect(resistor.n, inductor.p) annotation (Line(points={{-60,40},{-40,40}}, color={0,0,255}));
  connect(inductor.n, emf.p) annotation (Line(points={{-20,40},{0,40},{0,10}}, color={0,0,255}));
  connect(emf.n, n) annotation (Line(points={{0,-10},{0,-40},{-100,-40}}, color={0,0,255}));
  connect(emf.flange, rotor.flange_a) annotation (Line(points={{10,0},{30,0}}));
  connect(rotor.flange_b, flange) annotation (Line(points={{50,0},{100,0}}));
  connect(rotor.flange_b, friction.flange_a) annotation (Line(points={{50,0},{70,0},{70,-20}}));
  connect(friction.flange_b, housing.flange) annotation (Line(points={{70,-40},{70,-60}}));
  annotation (
    Icon(graphics={
      Rectangle(extent={{-70,50},{70,-50}}, lineColor={0,0,0}, fillColor={175,175,175},
        fillPattern=FillPattern.HorizontalCylinder),
      Rectangle(extent={{70,8},{100,-8}}, lineColor={0,0,0}, fillColor={160,160,164},
        fillPattern=FillPattern.HorizontalCylinder),
      Text(extent={{-60,20},{60,-20}}, textString="M", textColor={0,0,0}),
      Line(points={{-90,40},{-70,40}}, color={0,0,255}),
      Line(points={{-90,-40},{-70,-40}}, color={0,0,255}),
      Text(extent={{-150,100},{150,60}}, textString="%name", textColor={0,0,255})}),
    Documentation(info="<html>
<p>Klasyczny model silnika DC zbudowany z elementów MSL:</p>
<pre>  v = R·i + L·di/dt + k·&omega;        (obwód twornika)
  J·d&omega;/dt = k·i - b·&omega; - &tau;_load  (wirnik)</pre>
<p>Element <code>RotationalEMF</code> jest „przekładnią” między dziedzinami: zamienia prąd na moment
(<code>&tau; = k·i</code>) i prędkość na napięcie (<code>e = k·&omega;</code>). Ta sama stała <code>k</code>
w obu równaniach gwarantuje, że moc elektryczna <code>e·i</code> równa się mechanicznej <code>&tau;·&omega;</code>.</p>
<p><b>Dlaczego ten wariant, a nie <code>Modelica.Electrical.Machines.BasicMachines.DCMachines.DC_PermanentMagnet</code>:</b>
model z <code>Machines</code> wymaga rekordu danych znamionowych, ma straty w żelazie, szczotkach i zależność
od temperatury. Do nauki i do identyfikacji na stole wystarczy pięć parametrów (<code>R, L, k, J, b</code>),
które da się zmierzyć multimetrem, oscyloskopem i tachometrem, a diagram pokazuje każdy człon równania.</p>
<p>Wielkości charakterystyczne: prędkość bez obciążenia <code>&omega;_0 &asymp; U/k</code>,
prąd zwarcia (rozruchowy) <code>U/R</code>, moment utyku <code>k·U/R</code>, elektryczna stała czasowa <code>L/R</code>.</p>
</html>"));
end DCMotor;
