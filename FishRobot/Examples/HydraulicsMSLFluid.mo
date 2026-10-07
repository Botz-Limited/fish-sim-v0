within FishRobot.Examples;
model HydraulicsMSLFluid "Scenariusz 8 (opcja): obwód z HydraulicsStep na złączach Modelica.Fluid – do porównania"
  extends Modelica.Icons.Example;

  replaceable package Medium = Modelica.Media.Water.ConstantPropertyLiquidWater
    "Woda o stałych właściwościach (nieściśliwa)";

  parameter Modelica.Units.SI.AbsolutePressure p_ambient = 1.01325e5 "Ciśnienie otoczenia";
  parameter Modelica.Units.SI.Volume V_prefill = 8e-6
    "Wstępne napełnienie obu komór (PLACEHOLDER – do identyfikacji)";

  inner Modelica.Fluid.System system(
    p_ambient=p_ambient,
    T_ambient=293.15,
    energyDynamics=Modelica.Fluid.Types.Dynamics.FixedInitial,
    massDynamics=Modelica.Fluid.Types.Dynamics.FixedInitial,
    m_flow_small=1e-5,
    dp_small=1)
    "Ustawienia globalne Fluid. m_flow_small = 1e-5 kg/s: domyślne 1e-2 kg/s to rząd całego przepływu pompy"
    annotation (Placement(transformation(extent={{60,-80},{80,-60}})));

  // --- Elektryka (bez zmian względem HydraulicsStep)
  FishRobot.Electrical.Battery battery
    annotation (Placement(transformation(extent={{-130,-10},{-110,10}})));
  FishRobot.Electrical.HBridge bridge
    annotation (Placement(transformation(extent={{-100,-10},{-80,10}})));
  FishRobot.Electrical.DCMotor motor
    annotation (Placement(transformation(extent={{-60,-10},{-40,10}})));
  Modelica.Electrical.Analog.Basic.Ground ground
    annotation (Placement(transformation(extent={{-100,-60},{-80,-40}})));
  Modelica.Blocks.Sources.CombiTimeTable command(
    table=[0, 0; 0.1, 0; 0.2, 0.5; 2.0, 0.5; 2.1, 0; 3.0, 0])
    "Komenda u: rampa do 0,5, utrzymanie, rampa do zera"
    annotation (Placement(transformation(extent={{-130,30},{-110,50}})));

  // --- Hydraulika na złączach Modelica.Fluid
  FishRobot.HydraulicsFluid.GearPump pump(redeclare package Medium = Medium) "u > 0: przepływ z komory R do L"
    annotation (Placement(transformation(extent={{-10,-10},{10,10}}, rotation=90, origin={-20,0})));
  FishRobot.HydraulicsFluid.Pipe pipeL(redeclare package Medium = Medium) "Przewód pompa -> komora L"
    annotation (Placement(transformation(extent={{20,30},{40,50}})));
  FishRobot.HydraulicsFluid.Pipe pipeR(redeclare package Medium = Medium) "Przewód pompa -> komora R"
    annotation (Placement(transformation(extent={{20,-50},{40,-30}})));
  FishRobot.HydraulicsFluid.Chamber chamberL(redeclare package Medium = Medium,
    p_ambient=p_ambient, V_prefill=V_prefill) "Komora lewa"
    annotation (Placement(transformation(extent={{60,50},{80,70}})));
  FishRobot.HydraulicsFluid.Chamber chamberR(redeclare package Medium = Medium,
    p_ambient=p_ambient, V_prefill=V_prefill) "Komora prawa"
    annotation (Placement(transformation(extent={{60,-30},{80,-10}})));
  FishRobot.HydraulicsFluid.ReliefValve reliefLR(redeclare package Medium = Medium)
    "Zrzut L -> R przy nadciśnieniu po stronie L"
    annotation (Placement(transformation(extent={{-10,-10},{10,10}}, rotation=-90, origin={0,0})));
  FishRobot.HydraulicsFluid.ReliefValve reliefRL(redeclare package Medium = Medium)
    "Zrzut R -> L przy nadciśnieniu po stronie R"
    annotation (Placement(transformation(extent={{-10,-10},{10,10}}, rotation=90, origin={10,0})));

  // --- Wielkości do wykresów (te same nazwy co w HydraulicsStep)
  Modelica.Units.SI.PressureDifference p_L = chamberL.p_gauge "Nadciśnienie w komorze L";
  Modelica.Units.SI.PressureDifference p_R = chamberR.p_gauge "Nadciśnienie w komorze R";
  Modelica.Units.SI.VolumeFlowRate Q_pump = pump.Q "Przepływ przez pompę (R -> L)";
  Modelica.Units.SI.VolumeFlowRate Q_relief = (reliefLR.port_a.m_flow - reliefRL.port_a.m_flow)/pump.rho
    "Przepływ przez zawory (L -> R)";
  Modelica.Units.SI.Current i_motor = motor.i "Prąd silnika";
  Modelica.Units.SI.Current i_battery = battery.i "Prąd baterii";
  Modelica.Units.SI.Temperature T_L = chamberL.medium.T "Temperatura wody w komorze L (stan, którego lekki pakiet nie ma)";

equation
  connect(command.y[1], bridge.u) annotation (Line(points={{-109,40},{-90,40},{-90,12}}, color={0,0,127}));
  connect(battery.p, bridge.bat) annotation (Line(points={{-110,0},{-106,0},{-106,4},{-100,4}}, color={0,0,255}));
  connect(battery.n, bridge.n) annotation (Line(points={{-130,0},{-136,0},{-136,-24},{-90,-24},{-90,-10}}, color={0,0,255}));
  connect(bridge.mot, motor.p) annotation (Line(points={{-80,4},{-60,4}}, color={0,0,255}));
  connect(motor.n, bridge.n) annotation (Line(points={{-60,-4},{-70,-4},{-70,-24},{-90,-24},{-90,-10}}, color={0,0,255}));
  connect(ground.p, bridge.n) annotation (Line(points={{-90,-40},{-90,-10}}, color={0,0,255}));
  connect(motor.flange, pump.flange) annotation (Line(points={{-40,0},{-30,0}}));
  connect(pump.port_b, pipeL.port_a) annotation (Line(points={{-20,10},{-20,40},{20,40}}, color={0,127,255}));
  connect(pipeL.port_b, chamberL.ports[1]) annotation (Line(points={{40,40},{70,40},{70,50}}, color={0,127,255}));
  connect(pump.port_a, pipeR.port_a) annotation (Line(points={{-20,-10},{-20,-40},{20,-40}}, color={0,127,255}));
  connect(pipeR.port_b, chamberR.ports[1]) annotation (Line(points={{40,-40},{70,-40},{70,-30}}, color={0,127,255}));
  connect(reliefLR.port_a, pump.port_b) annotation (Line(points={{0,10},{0,20},{-20,20},{-20,10}}, color={0,127,255}));
  connect(reliefLR.port_b, pump.port_a) annotation (Line(points={{0,-10},{0,-20},{-20,-20},{-20,-10}}, color={0,127,255}));
  connect(reliefRL.port_a, pump.port_a) annotation (Line(points={{10,-10},{10,-20},{-20,-20},{-20,-10}}, color={0,127,255}));
  connect(reliefRL.port_b, pump.port_b) annotation (Line(points={{10,10},{10,20},{-20,20},{-20,10}}, color={0,127,255}));
  annotation (
    experiment(StopTime=3.0, Interval=0.001, Tolerance=1e-6),
    Diagram(coordinateSystem(extent={{-140,-80},{100,80}})),
    Documentation(info="<html>
<p><b>Scenariusz 8 (opcjonalny).</b> Ten sam obwód i ta sama komenda co w <code>HydraulicsStep</code>,
ale hydraulika jest zbudowana na złączach <code>Modelica.Fluid</code> z medium
<code>Modelica.Media.Water.ConstantPropertyLiquidWater</code> (komponenty z <code>FishRobot.HydraulicsFluid</code>).
Porównanie wyników i złożoności robi <code>scripts/compare_fluid.py</code>.</p>
<p><b>Na co zwrócić uwagę:</b></p>
<ul>
<li><code>inner Modelica.Fluid.System system</code> musi być w każdym modelu z Modelica.Fluid. Ustawia m.in. sposób
inicjalizacji bilansów i progi regularyzacji przepływu w okolicy zera. Domyślne <code>m_flow_small = 0,01 kg/s</code>
jest dobrane do instalacji przemysłowych; u nas to rząd całego przepływu pompy, więc je zmniejszamy. W tym obwodzie
akurat nie ma to wpływu: kryza wygładza charakterystykę według <code>dp_small</code>, a rura według liczby Reynoldsa.</li>
<li>Złącza przenoszą przepływ <b>masowy</b> i entalpię, więc model ma dodatkowe zmienne i stany (temperatura
w każdej komorze), choć przy wodzie o stałych właściwościach niczego nie zmieniają.</li>
<li>Z każdym portem komory można połączyć tylko jeden element (<code>nPorts</code>), bo naczynie
idealnie miesza strumienie.</li>
</ul>
</html>"));
end HydraulicsMSLFluid;
