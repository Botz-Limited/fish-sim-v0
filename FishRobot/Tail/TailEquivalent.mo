within FishRobot.Tail;
model TailEquivalent "Ogon 1 DOF: (J + J_added)·θ'' = τ_hyd - k·θ - c·θ' - c_h·|θ'|·θ'"
  parameter Real D_tail(unit="m3/rad") = 2e-5
    "Objętość wypierana na radian, = A_eff·r_eff (PLACEHOLDER – do identyfikacji)";
  parameter Modelica.Units.SI.Inertia J = 5e-4 "Moment bezwładności ogona (PLACEHOLDER – do identyfikacji)";
  parameter Modelica.Units.SI.Inertia J_added = 1e-3
    "Masa dodana wody (moment bezwładności) (PLACEHOLDER – do identyfikacji)";
  parameter Modelica.Units.SI.RotationalSpringConstant k = 2.0
    "Sztywność zginania ogona (PLACEHOLDER – do identyfikacji)";
  parameter Modelica.Units.SI.RotationalDampingConstant c = 5e-3
    "Tłumienie liniowe (materiał + lepkość) (PLACEHOLDER – do identyfikacji)";
  parameter Real c_h(unit="N.m.s2/rad2") = 1e-2
    "Tłumienie hydrodynamiczne kwadratowe (PLACEHOLDER – do identyfikacji)";
  parameter Modelica.Units.SI.Length L_tail = 0.1 "Długość ogona do końcówki (PLACEHOLDER – do identyfikacji)";
  parameter Modelica.Units.SI.Angle theta_start = 0 "Kąt początkowy";

  FishRobot.Interfaces.HydraulicPort_a port_L "Do komory L"
    annotation (Placement(transformation(extent={{-110,30},{-90,50}})));
  FishRobot.Interfaces.HydraulicPort_a port_R "Do komory R"
    annotation (Placement(transformation(extent={{-110,-50},{-90,-30}})));
  Modelica.Mechanics.Rotational.Interfaces.Flange_b flange
    "Oś ogona (np. do dodatkowego obciążenia lub pomiaru momentu)"
    annotation (Placement(transformation(extent={{90,-10},{110,10}})));
  Modelica.Blocks.Interfaces.RealOutput theta(unit="rad", displayUnit="deg") "Kąt ogona"
    annotation (Placement(transformation(extent={{-10,-10},{10,10}}, rotation=-90, origin={-20,-110})));
  Modelica.Blocks.Interfaces.RealOutput w(unit="rad/s") "Prędkość kątowa ogona"
    annotation (Placement(transformation(extent={{-10,-10},{10,10}}, rotation=-90, origin={20,-110})));

  Modelica.Units.SI.Torque tau_hyd = bender.tau_hyd "Moment od ciśnienia w komorach";
  Modelica.Units.SI.Velocity v_tip = L_tail*w "Prędkość boczna końcówki ogona";
  Modelica.Units.SI.Power P_hyd = bender.P_hyd "Moc hydrauliczna dostarczona do ogona";
  Modelica.Units.SI.Power P_water = springDamper.lossPower + hydroDamper.lossPower
    "Moc rozproszona w wodzie i materiale: c·θ'² + c_h·|θ'|·θ'²";
  Modelica.Units.SI.Energy E_kin = 0.5*(J + J_added)*w^2 "Energia kinetyczna ogona (z masą dodaną)";
  Modelica.Units.SI.Energy E_spring = 0.5*k*theta^2 "Energia sprężysta ogona";

  HydraulicBender bender(D_tail=D_tail)
    annotation (Placement(transformation(extent={{-60,-10},{-40,10}})));
  Modelica.Mechanics.Rotational.Components.Inertia body(J=J + J_added,
    phi(start=theta_start, fixed=true), w(start=0, fixed=true)) "Ogon + masa dodana wody"
    annotation (Placement(transformation(extent={{-10,-10},{10,10}})));
  Modelica.Mechanics.Rotational.Components.SpringDamper springDamper(c=k, d=c)
    "Sztywność i tłumienie liniowe"
    annotation (Placement(transformation(extent={{-10,-10},{10,10}}, rotation=-90, origin={40,-30})));
  QuadraticDamper hydroDamper(c_h=c_h) "Opór wody"
    annotation (Placement(transformation(extent={{60,30},{80,50}})));
  Modelica.Mechanics.Rotational.Components.Fixed fixed "Kadłub"
    annotation (Placement(transformation(extent={{30,-70},{50,-50}})));
equation
  connect(port_L, bender.port_L) annotation (Line(points={{-100,40},{-80,40},{-80,4},{-60,4}}, color={0,128,255}));
  connect(port_R, bender.port_R) annotation (Line(points={{-100,-40},{-80,-40},{-80,-4},{-60,-4}}, color={0,128,255}));
  connect(bender.flange, body.flange_a) annotation (Line(points={{-40,0},{-10,0}}));
  connect(body.flange_b, flange) annotation (Line(points={{10,0},{100,0}}));
  connect(body.flange_b, springDamper.flange_a) annotation (Line(points={{10,0},{40,0},{40,-20}}));
  connect(springDamper.flange_b, fixed.flange) annotation (Line(points={{40,-40},{40,-60}}));
  connect(body.flange_b, hydroDamper.flange) annotation (Line(points={{10,0},{50,0},{50,40},{60,40}}));
  theta = body.phi;
  w = body.w;
  annotation (
    Icon(graphics={
      Rectangle(extent={{-90,90},{90,-90}}, lineColor={0,0,0}, fillColor={255,255,255},
        fillPattern=FillPattern.Solid),
      Polygon(points={{-60,0},{40,30},{80,60},{70,0},{80,-60},{40,-30},{-60,0}}, lineColor={0,0,0},
        fillColor={255,170,85}, fillPattern=FillPattern.Solid),
      Text(extent={{-80,-50},{0,-80}}, textString="θ", textColor={0,0,0}),
      Text(extent={{-150,140},{150,100}}, textString="%name", textColor={0,0,255})}),
    Documentation(info="<html>
<p>Ogon sprowadzony do jednego stopnia swobody – kąta &theta; – z równaniem ruchu:</p>
<pre>  (J + J_added)·&theta;'' = &tau;_hyd - k·&theta; - c·&theta;' - c_h·|&theta;'|·&theta;'</pre>
<ul>
<li><code>&tau;_hyd = D_tail·(p_L - p_R)</code> – z przetwornika <code>HydraulicBender</code>,</li>
<li><code>J_added</code> – <b>masa dodana</b>: ogon, poruszając się, musi rozpędzić też otaczającą wodę.
Dla płaskiej płetwy może być większa niż bezwładność samego ogona,</li>
<li><code>k</code> – sztywność zginania (silikon, kręgosłup), <code>c</code> – tłumienie liniowe,</li>
<li><code>c_h</code> – opór wody rosnący z kwadratem prędkości.</li>
</ul>
<p>Wszystkie elementy to komponenty <code>Modelica.Mechanics.Rotational</code>, więc moce i momenty liczą się
same z połączeń. <b>Bilans energii ogona:</b> <code>P_hyd = d(E_kin + E_spring)/dt + P_water</code>.</p>
<p>Częstotliwość własna bez hydrauliki: <code>f<sub>0</sub> = &radic;(k/(J+J_added)) / 2&pi;</code>
(ok. 5,8 Hz dla placeholderów). Hydraulika dokłada sztywność komór, przeliczoną na kąt jako
<code>D_tail<sup>2</sup>·dp/dV</code>.</p>
<p><code>J_added</code>, <code>c_h</code> i <code>D_tail</code> to placeholdery – patrz plan kalibracji w README.</p>
</html>"));
end TailEquivalent;
