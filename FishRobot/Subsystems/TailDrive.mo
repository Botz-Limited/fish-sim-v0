within FishRobot.Subsystems;
model TailDrive "Napęd ogona: bateria + mostek H + silnik + pompa + przewody + komory + zawory + ogon"
  parameter Modelica.Units.SI.AbsolutePressure p_ambient = 1.01325e5 "Ciśnienie otoczenia";
  parameter Modelica.Units.SI.Volume V_prefill = 8e-6
    "Wstępne napełnienie obu komór (PLACEHOLDER – do identyfikacji)";
  parameter Modelica.Units.SI.PressureDifference p_set = 50e3
    "Ciśnienie otwarcia zaworów przelewowych (PLACEHOLDER – do identyfikacji)";

  // --- Wejście i wyjścia (interfejs FMU)
  Modelica.Blocks.Interfaces.RealInput u "Komenda pompy u ∈ [-1, 1]"
    annotation (Placement(transformation(extent={{-140,-20},{-100,20}})));
  Modelica.Blocks.Interfaces.RealOutput theta(unit="rad") "Kąt ogona"
    annotation (Placement(transformation(extent={{100,70},{120,90}})));
  Modelica.Blocks.Interfaces.RealOutput w_tail(unit="rad/s") "Prędkość kątowa ogona"
    annotation (Placement(transformation(extent={{100,40},{120,60}})));
  Modelica.Blocks.Interfaces.RealOutput tau_tail(unit="N.m") "Moment hydrauliczny na ogonie"
    annotation (Placement(transformation(extent={{100,10},{120,30}})));
  Modelica.Blocks.Interfaces.RealOutput p_L(unit="Pa") "Nadciśnienie w komorze L"
    annotation (Placement(transformation(extent={{100,-20},{120,0}})));
  Modelica.Blocks.Interfaces.RealOutput p_R(unit="Pa") "Nadciśnienie w komorze R"
    annotation (Placement(transformation(extent={{100,-50},{120,-30}})));
  Modelica.Blocks.Interfaces.RealOutput i_motor(unit="A") "Prąd silnika pompy"
    annotation (Placement(transformation(extent={{100,-80},{120,-60}})));

  // --- Elektryka
  FishRobot.Electrical.Battery battery
    annotation (Placement(transformation(extent={{-90,-50},{-70,-30}})));
  FishRobot.Electrical.HBridge bridge
    annotation (Placement(transformation(extent={{-60,-50},{-40,-30}})));
  FishRobot.Electrical.DCMotor motor
    annotation (Placement(transformation(extent={{-30,-50},{-10,-30}})));
  Modelica.Electrical.Analog.Basic.Ground ground
    annotation (Placement(transformation(extent={{-60,-90},{-40,-70}})));

  // --- Hydraulika
  FishRobot.Hydraulics.GearPump pump "u > 0: przepływ z komory R do L"
    annotation (Placement(transformation(extent={{-10,10},{10,-10}}, rotation=90, origin={10,-40})));
  FishRobot.Hydraulics.Pipe pipeL "Przewód pompa -> komora L"
    annotation (Placement(transformation(extent={{30,10},{50,30}})));
  FishRobot.Hydraulics.Pipe pipeR "Przewód pompa -> komora R"
    annotation (Placement(transformation(extent={{30,-80},{50,-60}})));
  FishRobot.Hydraulics.Chamber chamberL(p_ambient=p_ambient, V_prefill=V_prefill) "Komora lewa"
    annotation (Placement(transformation(extent={{50,40},{70,60}})));
  FishRobot.Hydraulics.Chamber chamberR(p_ambient=p_ambient, V_prefill=V_prefill) "Komora prawa"
    annotation (Placement(transformation(extent={{50,-50},{70,-30}})));
  FishRobot.Hydraulics.ReliefValve reliefLR(p_set=p_set) "Zrzut L -> R"
    annotation (Placement(transformation(extent={{-10,-10},{10,10}}, rotation=-90, origin={-10,0})));
  FishRobot.Hydraulics.ReliefValve reliefRL(p_set=p_set) "Zrzut R -> L"
    annotation (Placement(transformation(extent={{-10,-10},{10,10}}, rotation=90, origin={-30,0})));

  // --- Ogon
  FishRobot.Tail.TailEquivalent tail
    annotation (Placement(transformation(extent={{70,-10},{90,10}})));

equation
  connect(u, bridge.u) annotation (Line(points={{-120,0},{-50,0},{-50,-28}}, color={0,0,127}));
  connect(battery.p, bridge.bat) annotation (Line(points={{-70,-40},{-66,-40},{-66,-36},{-60,-36}}, color={0,0,255}));
  connect(battery.n, bridge.n) annotation (Line(points={{-90,-40},{-94,-40},{-94,-60},{-50,-60},{-50,-50}}, color={0,0,255}));
  connect(bridge.mot, motor.p) annotation (Line(points={{-40,-36},{-30,-36}}, color={0,0,255}));
  connect(motor.n, bridge.n) annotation (Line(points={{-30,-44},{-34,-44},{-34,-60},{-50,-60},{-50,-50}}, color={0,0,255}));
  connect(ground.p, bridge.n) annotation (Line(points={{-50,-70},{-50,-50}}, color={0,0,255}));
  connect(motor.flange, pump.flange) annotation (Line(points={{-10,-40},{0,-40}}));
  connect(pump.port_b, pipeL.port_a) annotation (Line(points={{10,-30},{10,20},{30,20}}, color={0,128,255}));
  connect(pump.port_a, pipeR.port_a) annotation (Line(points={{10,-50},{10,-70},{30,-70}}, color={0,128,255}));
  connect(pipeL.port_b, chamberL.port) annotation (Line(points={{50,20},{60,20},{60,40}}, color={0,128,255}));
  connect(pipeR.port_b, chamberR.port) annotation (Line(points={{50,-70},{60,-70},{60,-50}}, color={0,128,255}));
  connect(pipeL.port_b, tail.port_L) annotation (Line(points={{50,20},{64,20},{64,4},{70,4}}, color={0,128,255}));
  connect(pipeR.port_b, tail.port_R) annotation (Line(points={{50,-70},{66,-70},{66,-4},{70,-4}}, color={0,128,255}));
  connect(reliefLR.port_a, pump.port_b) annotation (Line(points={{-10,10},{-10,20},{10,20},{10,-30}}, color={0,128,255}));
  connect(reliefLR.port_b, pump.port_a) annotation (Line(points={{-10,-10},{-10,-20},{4,-20},{4,-56},{10,-56},{10,-50}}, color={0,128,255}));
  connect(reliefRL.port_a, pump.port_a) annotation (Line(points={{-30,-10},{-30,-20},{4,-20},{4,-56},{10,-56},{10,-50}}, color={0,128,255}));
  connect(reliefRL.port_b, pump.port_b) annotation (Line(points={{-30,10},{-30,20},{10,20},{10,-30}}, color={0,128,255}));
  theta = tail.theta;
  w_tail = tail.w;
  tau_tail = tail.tau_hyd;
  p_L = chamberL.p_gauge;
  p_R = chamberR.p_gauge;
  i_motor = motor.i;
  annotation (
    Icon(graphics={
      Rectangle(extent={{-100,100},{100,-100}}, lineColor={0,0,0}, fillColor={240,248,255},
        fillPattern=FillPattern.Solid),
      Text(extent={{-90,60},{90,20}}, textString="M → P", textColor={0,0,0}),
      Polygon(points={{-20,-20},{40,0},{60,20},{55,-20},{60,-60},{40,-40},{-20,-20}}, lineColor={0,0,0},
        fillColor={255,170,85}, fillPattern=FillPattern.Solid),
      Text(extent={{-150,150},{150,110}}, textString="%name", textColor={0,0,255})}),
    Documentation(info="<html>
<p>Cały napęd ogona w jednym bloku z wejściem <code>u</code> i wyjściami sygnałowymi – to jest podukład
eksportowany jako FMU w etapie 8. Wewnątrz: bateria &rarr; mostek H &rarr; silnik DC &rarr; pompa zębata &rarr;
przewody &rarr; komory L/R (z zaworami przelewowymi przeciwsobnymi przy pompie) &rarr; ogon 1 DOF.</p>
<p>Wszystkie komponenty są publiczne, więc parametry można zmieniać modyfikatorami, np.
<code>TailDrive drive(motor(R=0.8), tail(k=0.4))</code>, a w OMEdit przez okno parametrów.</p>
<p>Konwencja: <code>u &gt; 0</code> &rArr; pompa tłoczy R &rarr; L &rArr; <code>p_L &gt; p_R</code> &rArr; <code>&theta; &gt; 0</code>.</p>
</html>"));
end TailDrive;
