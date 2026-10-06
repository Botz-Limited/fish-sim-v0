within FishRobot.Examples;
model TailFlapping "Scenariusz 2: sinusoidalna komenda pompy, ogon swobodny"
  extends Modelica.Icons.Example;
  FishRobot.Control.CPG cpg(A=0.8, f=1.0)
    annotation (Placement(transformation(extent={{-60,-10},{-40,10}})));
  FishRobot.Subsystems.TailDrive drive
    annotation (Placement(transformation(extent={{-10,-10},{10,10}})));
equation
  connect(cpg.y, drive.u) annotation (Line(points={{-39,0},{-12,0}}, color={0,0,127}));
  annotation (
    experiment(StopTime=5.0, Interval=0.001, Tolerance=1e-6),
    Documentation(info="<html>
<p><b>Scenariusz 2.</b> CPG podaje sinus 1 Hz o amplitudzie 0,8. Pompa na przemian napełnia komorę L i R,
ogon macha. Obserwuj: opóźnienie fazowe kąta względem komendy (pompa musi najpierw przetłoczyć ciecz),
asymetrię prądu przy przyspieszaniu i hamowaniu oraz to, że ciśnienia w komorach są przesunięte w fazie
względem kąta (część momentu idzie na bezwładność i tłumienie, nie tylko na sprężynę).</p>
</html>"));
end TailFlapping;
