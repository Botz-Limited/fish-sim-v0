within FishRobot.Tests;
model TailDriveDirection "Test konwencji: dodatnia komenda pompy -> dodatni kąt ogona"
  extends Modelica.Icons.Example;
  Modelica.Blocks.Sources.Step command(height=0.3, startTime=0.1)
    annotation (Placement(transformation(extent={{-60,-10},{-40,10}})));
  FishRobot.Subsystems.TailDrive drive
    annotation (Placement(transformation(extent={{-10,-10},{10,10}})));
  Modelica.Units.SI.Volume V_total = drive.chamberL.V + drive.chamberR.V
    "Objętość obu komór (ogon wypiera tyle samo z jednej strony, ile zasysa z drugiej)";
equation
  connect(command.y, drive.u) annotation (Line(points={{-39,0},{-12,0}}, color={0,0,127}));
  annotation (
    experiment(StopTime=1.0, Interval=0.001, Tolerance=1e-6),
    Documentation(info="<html>
<p>Stała komenda <code>u = 0,3</code>. Oczekiwania: <code>&theta; &gt; 0</code>, <code>p_L &gt; p_R</code>,
moment hydrauliczny dodatni, suma objętości komór stała.</p>
</html>"));
end TailDriveDirection;
