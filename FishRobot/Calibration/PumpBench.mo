within FishRobot.Calibration;
model PumpBench "Stanowisko: pompa napędzana silnikiem z kroku 2, wylot przez zawór dławiący do zbiornika (krok 3)"
  extends Modelica.Icons.Example;

  parameter Modelica.Units.SI.Voltage U = 6.0 "Napięcie zasilacza";
  parameter Real G_throttle(unit="m3/(s.Pa)") = 1e-9 "Przewodność zaworu dławiącego (nastawa iglicy)";

  Modelica.Electrical.Analog.Sources.ConstantVoltage supply(V=U) "Zasilacz laboratoryjny"
    annotation (Placement(transformation(extent={{-10,-10},{10,10}}, rotation=-90, origin={-70,0})));
  Modelica.Electrical.Analog.Basic.Ground ground
    annotation (Placement(transformation(extent={{-80,-50},{-60,-30}})));
  FishRobot.Electrical.DCMotor motor "Silnik zidentyfikowany w kroku 2 – służy jako czujnik momentu"
    annotation (Placement(transformation(extent={{-40,-10},{-20,10}})));
  FishRobot.Hydraulics.GearPump pump
    annotation (Placement(transformation(extent={{0,-10},{20,10}})));
  FishRobot.Hydraulics.Reservoir tank "Zbiornik otwarty (wlot pompy i powrót z zaworu)"
    annotation (Placement(transformation(extent={{-20,-50},{0,-30}})));
  FishRobot.Calibration.LinearThrottle throttle(G=G_throttle)
    annotation (Placement(transformation(extent={{40,-10},{60,10}})));

  // Wielkości mierzone: prąd, prędkość wału, przyrost ciśnienia na pompie (czujnik różnicowy), przepływ
  Modelica.Units.SI.Current i = motor.i "Prąd silnika";
  Modelica.Units.SI.AngularVelocity w = motor.w "Prędkość wału";
  Modelica.Units.SI.PressureDifference dp = pump.dp_pump "Przyrost ciśnienia na pompie";
  Modelica.Units.SI.VolumeFlowRate Q = pump.V_flow "Przepływ (przepływomierz na wylocie)";
equation
  connect(supply.p, motor.p) annotation (Line(points={{-70,10},{-70,20},{-46,20},{-46,4},{-40,4}}, color={0,0,255}));
  connect(supply.n, motor.n) annotation (Line(points={{-70,-10},{-70,-20},{-46,-20},{-46,-4},{-40,-4}}, color={0,0,255}));
  connect(ground.p, supply.n) annotation (Line(points={{-70,-30},{-70,-10}}, color={0,0,255}));
  connect(motor.flange, pump.flange) annotation (Line(points={{-20,0},{-10,0},{-10,20},{10,20},{10,10}}));
  connect(tank.port, pump.port_a) annotation (Line(points={{0,-40},{0,0}}, color={0,128,255}));
  connect(pump.port_b, throttle.port_a) annotation (Line(points={{20,0},{40,0}}, color={0,128,255}));
  connect(throttle.port_b, tank.port) annotation (Line(points={{60,0},{70,0},{70,-40},{0,-40}}, color={0,128,255}));
  annotation (
    experiment(StopTime=0.5, Interval=1e-3, Tolerance=1e-8),
    Documentation(info="<html>
<p>Pompa kręcona silnikiem z kroku 2 tłoczy wodę ze zbiornika przez zawór dławiący z powrotem do zbiornika.
Punkt pracy ustawia się napięciem zasilacza i nastawą zaworu. W każdym punkcie, po ustaleniu się prędkości,
mierzymy <code>i, w, &Delta;p, Q</code>. Równania pompy są liniowe w szukanych parametrach:</p>
<pre>  Q            = D·w - k_leak·&Delta;p      -> D_rev = 2&pi;·D, k_leak
  k·i - b·w    = D·&Delta;p/&eta;_m          -> &eta;_m (tryb pompy, &Delta;p &gt; 0)</pre>
<p>Lewa strona drugiego równania to moment na wale policzony z prądu silnika. Dlatego silnik trzeba
zidentyfikować wcześniej, a jego niepewność (zwłaszcza <code>b</code>) przenosi się na <code>&eta;_m</code>.</p>
</html>"));
end PumpBench;
