within FishRobot.Examples;
model DepthControl "Scenariusz 6: skoki zadanej głębokości -0,5 -> -1,5 -> -1,0 m"
  extends Modelica.Icons.Example;
  FishRobot.Electrical.Battery battery
    annotation (Placement(transformation(extent={{-90,-60},{-70,-40}})));
  Modelica.Electrical.Analog.Basic.Ground ground
    annotation (Placement(transformation(extent={{-50,-100},{-30,-80}})));
  Modelica.Blocks.Sources.CombiTimeTable depthReference(
    table=[0, -0.5; 10, -0.5; 10, -1.5; 100, -1.5; 100, -1.0; 200, -1.0],
    smoothness=Modelica.Blocks.Types.Smoothness.ConstantSegments) "Zadana głębokość"
    annotation (Placement(transformation(extent={{-90,30},{-70,50}})));
  FishRobot.Control.DepthPID controller(V_max=syringe.V_max, V_ff=5.5e-6)
    "Sprzężenie w przód celowo niedokładne (5,5 ml zamiast 6 ml) – błąd usunie całka"
    annotation (Placement(transformation(extent={{-50,0},{-30,20}})));
  FishRobot.Buoyancy.BallastSyringe syringe(x_start=controller.V_ff/syringe.A_piston)
    "Start z pęcherzem w położeniu, które regulator uważa za neutralne"
    annotation (Placement(transformation(extent={{-10,-30},{10,-10}})));
  FishRobot.Buoyancy.VerticalDynamics fish(z_start=-0.5)
    annotation (Placement(transformation(extent={{30,-30},{50,-10}})));
  Modelica.Blocks.Math.Gain toDepth(k=-1) "z -> głębokość (dodatnia)"
    annotation (Placement(transformation(extent={{40,-70},{20,-50}})));
equation
  connect(depthReference.y[1], controller.z_ref) annotation (Line(points={{-69,40},{-60,40},{-60,16},{-52,16}}, color={0,0,127}));
  connect(fish.z, controller.z) annotation (Line(points={{51,-16},{60,-16},{60,30},{-56,30},{-56,10},{-52,10}}, color={0,0,127}));
  connect(syringe.V_b, controller.V_b) annotation (Line(points={{11,-20},{20,-20},{20,0},{-60,0},{-60,4},{-52,4}}, color={0,0,127}));
  connect(controller.u, syringe.u) annotation (Line(points={{-29,10},{-20,10},{-20,-14},{-12,-14}}, color={0,0,127}));
  connect(syringe.V_b, fish.V_b) annotation (Line(points={{11,-20},{28,-20}}, color={0,0,127}));
  connect(fish.z, toDepth.u) annotation (Line(points={{51,-16},{60,-16},{60,-60},{42,-60}}, color={0,0,127}));
  connect(toDepth.y, syringe.depth) annotation (Line(points={{19,-60},{-16,-60},{-16,-26},{-12,-26}}, color={0,0,127}));
  connect(battery.p, syringe.bat) annotation (Line(points={{-70,-50},{-20,-50},{-20,-20},{-10,-20}}, color={0,0,255}));
  connect(battery.n, syringe.n) annotation (Line(points={{-90,-50},{-94,-50},{-94,-76},{0,-76},{0,-30}}, color={0,0,255}));
  connect(ground.p, syringe.n) annotation (Line(points={{-40,-80},{-40,-76},{0,-76},{0,-30}}, color={0,0,255}));
  annotation (
    experiment(StopTime=200, Interval=0.05, Tolerance=1e-6),
    Documentation(info="<html>
<p><b>Scenariusz 6.</b> Ryba startuje na -0,5 m z pęcherzem 5,5 ml – tyle, ile regulator szacuje jako neutralne
(naprawdę neutralne jest 6 ml, więc ryba jest odrobinę za ciężka i na początku powoli tonie, aż całka to wyrówna). Zadana głębokość: -1,5 m od t = 10 s,
-1,0 m od t = 100 s. Regulator kaskadowy <code>DepthPID</code> zmienia objętość pęcherza strzykawką.</p>
<p>Obserwuj: żeby zanurzyć się głębiej, regulator najpierw <b>zmniejsza</b> pęcherz (ryba robi się cięższa), a przed
celem <b>zwiększa</b> go z powrotem, żeby wyhamować (człon D). Na końcu objętość ustala się na wartości neutralnej, mimo że
sprzężenie w przód zakłada 5,5 ml zamiast 6 ml – różnicę wyrównuje człon całkujący. Prąd silnika strzykawki płynie tylko
podczas ruchu tłoka.</p>
</html>"));
end DepthControl;
