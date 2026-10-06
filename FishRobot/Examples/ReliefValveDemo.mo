within FishRobot.Examples;
model ReliefValveDemo "Scenariusz 4: za duża amplituda komendy – zawór przelewowy otwiera się i traci energię"
  extends Modelica.Icons.Example;
  FishRobot.Control.CPG cpg(A=1.0, f=0.25)
    annotation (Placement(transformation(extent={{-60,-10},{-40,10}})));
  FishRobot.Subsystems.TailDrive drive
    annotation (Placement(transformation(extent={{-10,-10},{10,10}})));
  Modelica.Units.SI.Power P_relief = drive.reliefLR.P_loss + drive.reliefRL.P_loss "Moc tracona w zaworach";
  Modelica.Units.SI.Energy E_relief(start=0, fixed=true) "Energia stracona w zaworach";
  Modelica.Units.SI.Energy E_pump_hyd(start=0, fixed=true) "Energia hydrauliczna oddana przez pompę";
equation
  der(E_relief) = P_relief;
  der(E_pump_hyd) = drive.pump.P_hyd;
  connect(cpg.y, drive.u) annotation (Line(points={{-39,0},{-12,0}}, color={0,0,127}));
  annotation (
    experiment(StopTime=20.0, Interval=0.002, Tolerance=1e-6),
    Documentation(info="<html>
<p><b>Scenariusz 4.</b> Pełna komenda (A = 1) przy niskiej częstotliwości 0,25 Hz: pompa ma dość czasu,
żeby wytworzyć różnicę ciśnień ponad <code>p_set</code>. Zawór otwiera się w każdym półokresie, kąt ogona
przestaje rosnąć („spłaszczone” szczyty), a pompa dalej pracuje – tylko że jej moc idzie w ciepło w zaworze.</p>
<p>Wniosek projektowy: przy niskich częstotliwościach amplitudę komendy trzeba ograniczyć
(albo sterować ciśnieniem), bo inaczej bateria grzeje zawór.</p>
</html>"));
end ReliefValveDemo;
