within FishRobot.Tests;
model TailBlocked "Test: zablokowany ogon – zawór przelewowy przejmuje cały stały wydatek pompy"
  extends Modelica.Icons.Example;
  Modelica.Blocks.Sources.Constant command(k=1) "Pompa pracuje, zawory R -> L"
    annotation (Placement(transformation(extent={{-60,-10},{-40,10}})));
  FishRobot.Subsystems.TailDrive drive
    annotation (Placement(transformation(extent={{-10,-10},{10,10}})));
  Modelica.Mechanics.Rotational.Components.SpringDamper tailLock(c=1e3, d=10)
    "Bardzo sztywna blokada osi ogona (np. ogon przytrzymany ręką)"
    annotation (Placement(transformation(extent={{-10,-10},{10,10}}, rotation=-90, origin={0,-40})));
  Modelica.Mechanics.Rotational.Components.Fixed fixed
    annotation (Placement(transformation(extent={{-10,-80},{10,-60}})));
equation
  connect(command.y, drive.u) annotation (Line(points={{-39,0},{-12,0}}, color={0,0,127}));
  connect(drive.flange_tail, tailLock.flange_a) annotation (Line(points={{0,-10},{0,-30}}));
  connect(tailLock.flange_b, fixed.flange) annotation (Line(points={{0,-50},{0,-70}}));
  annotation (
    experiment(StopTime=1.0, Interval=0.001, Tolerance=1e-6),
    Documentation(info="<html>
<p>Pompa o stałych obrotach nie może przestać tłoczyć, a zawory 3/2 nie mają położenia zamkniętego. Gdy ogon
nie może się ruszyć, cały wydatek pompy musi uciec przez zawór przelewowy między tłoczeniem a ssaniem.
Oczekiwania: przyrost ciśnienia na pompie nie przekracza <code>p_set + dp_open</code>, a w stanie ustalonym
przepływ przez zawór przelewowy równa się wydatkowi pompy. Cała moc hydrauliczna pompy idzie wtedy w ciepło.</p>
</html>"));
end TailBlocked;
