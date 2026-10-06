within FishRobot.Tests;
model ChamberTableFromFile "Test: krzywa p–V z pliku CSV daje to samo co tabela w parametrze"
  extends Modelica.Icons.Example;

  Modelica.Blocks.Sources.Sine sine(amplitude=1e-5, f=0.5) "Przepływ ±10 ml/s"
    annotation (Placement(transformation(extent={{-90,-10},{-70,10}})));
  FishRobot.Hydraulics.VolumeFlowSource sourceTable
    annotation (Placement(transformation(extent={{-40,20},{-20,40}})));
  FishRobot.Hydraulics.VolumeFlowSource sourceFile
    annotation (Placement(transformation(extent={{-40,-40},{-20,-20}})));
  FishRobot.Hydraulics.Chamber chamberTable "Krzywa z parametru table"
    annotation (Placement(transformation(extent={{10,40},{30,60}})));
  FishRobot.Hydraulics.Chamber chamberFile(
    tableOnFile=true,
    fileName=Modelica.Utilities.Files.loadResource(
      "modelica://FishRobot/Resources/Data/chamber_pV_placeholder.csv")) "Ta sama krzywa z pliku CSV"
    annotation (Placement(transformation(extent={{10,-20},{30,0}})));
equation
  connect(sine.y, sourceTable.V_flow) annotation (Line(points={{-69,0},{-50,0},{-50,30},{-44,30}}, color={0,0,127}));
  connect(sine.y, sourceFile.V_flow) annotation (Line(points={{-69,0},{-50,0},{-50,-30},{-44,-30}}, color={0,0,127}));
  connect(sourceTable.port, chamberTable.port) annotation (Line(points={{-20,30},{20,30},{20,40}}, color={0,128,255}));
  connect(sourceFile.port, chamberFile.port) annotation (Line(points={{-20,-30},{20,-30},{20,-20}}, color={0,128,255}));
  annotation (
    experiment(StopTime=2.0, Interval=0.002, Tolerance=1e-8),
    Documentation(info="<html>
<p>Pokazuje, jak podmienić krzywą p–V komory na dane z pliku (np. z demo SOFA lub z pomiaru):
<code>tableOnFile = true</code> i ścieżka przez <code>loadResource(\"modelica://FishRobot/Resources/Data/...\")</code>,
która działa niezależnie od katalogu roboczego. Plik zawiera tę samą placeholderową krzywą co parametr
<code>table</code>, więc oba ciśnienia muszą być identyczne.</p>
</html>"));
end ChamberTableFromFile;
