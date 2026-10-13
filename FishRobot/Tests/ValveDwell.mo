within FishRobot.Tests;
model ValveDwell "Test: każdy stan zaworu trwa ≥ valve_min_dwell; częstotliwość przycinana do [tail_freq_min, tail_freq_max]"
  extends Modelica.Icons.Example;
  FishRobot.Control.CPG cpgMin(A_V=4e-6, f=0.5) "f poniżej zakresu -> f_eff = tail_freq_min"
    annotation (Placement(transformation(extent={{-60,40},{-40,60}})));
  FishRobot.Subsystems.TailDrive driveMin
    annotation (Placement(transformation(extent={{-10,40},{10,60}})));
  FishRobot.Control.CPG cpgMid(A_V=4e-6, f=2.0) "f w zakresie – bez zmian"
    annotation (Placement(transformation(extent={{-60,-10},{-40,10}})));
  FishRobot.Subsystems.TailDrive driveMid
    annotation (Placement(transformation(extent={{-10,-10},{10,10}})));
  FishRobot.Control.CPG cpgMax(A_V=4e-6, f=3.0) "f powyżej zakresu -> f_eff = tail_freq_max"
    annotation (Placement(transformation(extent={{-60,-60},{-40,-40}})));
  FishRobot.Subsystems.TailDrive driveMax
    annotation (Placement(transformation(extent={{-10,-60},{10,-40}})));
equation
  connect(cpgMin.y, driveMin.u) annotation (Line(points={{-39,50},{-12,50}}, color={0,0,127}));
  connect(driveMin.V_p, cpgMin.V_p) annotation (Line(points={{11,40},{20,40},{20,30},{-70,30},{-70,50},{-62,50}}, color={0,0,127}));
  connect(cpgMid.y, driveMid.u) annotation (Line(points={{-39,0},{-12,0}}, color={0,0,127}));
  connect(driveMid.V_p, cpgMid.V_p) annotation (Line(points={{11,-10},{20,-10},{20,-20},{-70,-20},{-70,0},{-62,0}}, color={0,0,127}));
  connect(cpgMax.y, driveMax.u) annotation (Line(points={{-39,-50},{-12,-50}}, color={0,0,127}));
  connect(driveMax.V_p, cpgMax.V_p) annotation (Line(points={{11,-60},{20,-60},{20,-70},{-70,-70},{-70,-50},{-62,-50}}, color={0,0,127}));
  annotation (
    experiment(StopTime=10.0, Interval=0.001, Tolerance=1e-6),
    Documentation(info="<html>
<p>Trzy napędy ogona z regulatorem przekaźnikowym: <code>f = 0,5 Hz</code> (przycięte do <code>tail_freq_min = 1,5 Hz</code>),
<code>f = 2 Hz</code> i <code>f = 3 Hz</code> (przycięte do <code>tail_freq_max = 2,5 Hz</code>). Oczekiwania
(<code>scripts/check_tests.py</code>): <code>f_eff</code> równe granicom zakresu, najkrótszy odstęp między przełączeniami
zaworów &ge; <code>valve_min_dwell</code> (0,2 s) dla każdej częstotliwości oraz
<code>tail_freq_max &le; 1/(2·valve_min_dwell)</code>.</p>
</html>"));
end ValveDwell;
