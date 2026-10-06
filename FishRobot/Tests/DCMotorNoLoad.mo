within FishRobot.Tests;
model DCMotorNoLoad "Test: rozruch silnika bez obciążenia przez mostek H – prędkość ustalona i bilans mocy"
  extends Modelica.Icons.Example;

  parameter Real u = 0.6 "Stała komenda mostka";

  FishRobot.Electrical.Battery battery
    annotation (Placement(transformation(extent={{-80,-10},{-60,10}})));
  FishRobot.Electrical.HBridge bridge
    annotation (Placement(transformation(extent={{-30,-10},{-10,10}})));
  FishRobot.Electrical.DCMotor motor
    annotation (Placement(transformation(extent={{20,-10},{40,10}})));
  Modelica.Electrical.Analog.Basic.Ground ground
    annotation (Placement(transformation(extent={{-30,-50},{-10,-30}})));
  Modelica.Blocks.Sources.Constant command(k=u)
    annotation (Placement(transformation(extent={{-60,30},{-40,50}})));

  // Stan ustalony: silnik widzi źródło u·U_nom o rezystancji R + u²·R_int (rezystancja baterii
  // „przetransformowana” przez mostek), a moment k·i równoważy tarcie b·w.
  parameter Real R_tot = motor.R + u^2*battery.R_int;
  parameter Modelica.Units.SI.AngularVelocity w_analytic =
    motor.k*u*battery.U_nom/(motor.k^2 + R_tot*motor.b) "Prędkość ustalona analitycznie";
  Modelica.Units.SI.Power P_balance_error = battery.P_chem - (battery.P_loss + motor.P_cu + motor.P_fric
    + motor.J*motor.w*der(motor.w) + motor.L*motor.i*der(motor.i))
    "Bilans mocy: ogniwo = straty + przyrost energii kinetycznej i magnetycznej (powinno być 0)";
equation
  connect(battery.p, bridge.bat) annotation (Line(points={{-60,0},{-50,0},{-50,4},{-30,4}}, color={0,0,255}));
  connect(battery.n, bridge.n) annotation (Line(points={{-80,0},{-90,0},{-90,-20},{-20,-20},{-20,-10}}, color={0,0,255}));
  connect(bridge.mot, motor.p) annotation (Line(points={{-10,4},{20,4}}, color={0,0,255}));
  connect(motor.n, bridge.n) annotation (Line(points={{20,-4},{10,-4},{10,-20},{-20,-20},{-20,-10}}, color={0,0,255}));
  connect(ground.p, bridge.n) annotation (Line(points={{-20,-30},{-20,-10}}, color={0,0,255}));
  connect(command.y, bridge.u) annotation (Line(points={{-39,40},{-20,40},{-20,12}}, color={0,0,127}));
  annotation (
    experiment(StopTime=0.5, Interval=0.0005, Tolerance=1e-8),
    Documentation(info="<html>
<p>Silnik bez obciążenia, zasilany z baterii przez mostek H z komendą <code>u = 0,6</code>.
Oczekiwania: prędkość ustalona zgodna ze wzorem
<code>&omega; = k·u·U / (k<sup>2</sup> + (R + u<sup>2</sup>·R_int)·b)</code> (&lt; 1%) oraz
zamknięty bilans mocy w każdej chwili, także w czasie rozruchu.</p>
<p>Ciekawostka: przez mostek rezystancja baterii „widziana” od strony silnika maleje do
<code>u<sup>2</sup>·R_int</code> – tak samo jak impedancja po drugiej stronie transformatora.</p>
</html>"));
end DCMotorNoLoad;
