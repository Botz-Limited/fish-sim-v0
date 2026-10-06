within FishRobot.Tests;
model ReliefValveLimit "Test: zawór przelewowy ogranicza ciśnienie w napełnianej komorze"
  extends Modelica.Icons.Example;

  Modelica.Blocks.Sources.Ramp ramp(height=valve.V_flow_nominal, duration=1)
    annotation (Placement(transformation(extent={{-90,-10},{-70,10}})));
  FishRobot.Hydraulics.VolumeFlowSource source
    annotation (Placement(transformation(extent={{-60,-10},{-40,10}})));
  FishRobot.Hydraulics.Chamber chamber
    annotation (Placement(transformation(extent={{-10,30},{10,50}})));
  FishRobot.Hydraulics.ReliefValve valve
    annotation (Placement(transformation(extent={{10,-10},{30,10}})));
  FishRobot.Hydraulics.Reservoir ambient "Otoczenie (zrzut z zaworu)"
    annotation (Placement(transformation(extent={{80,-10},{60,10}})));
equation
  connect(ramp.y, source.V_flow) annotation (Line(points={{-69,0},{-64,0}}, color={0,0,127}));
  connect(source.port, valve.port_a) annotation (Line(points={{-40,0},{10,0}}, color={0,128,255}));
  connect(chamber.port, valve.port_a) annotation (Line(points={{0,30},{0,0},{10,0}}, color={0,128,255}));
  connect(valve.port_b, ambient.port) annotation (Line(points={{30,0},{60,0}}, color={0,128,255}));
  annotation (
    experiment(StopTime=3.0, Interval=0.002, Tolerance=1e-8),
    Documentation(info="<html>
<p>Pompa (tu idealne źródło przepływu) wtłacza coraz więcej cieczy do komory, aż do przepływu
nominalnego zaworu. Ciśnienie rośnie zgodnie z krzywą p–V, aż zawór zacznie upuszczać ciecz.</p>
<p>Oczekiwania: nadciśnienie nie przekracza <code>p_set + dp_open</code>, a w stanie ustalonym
cały przepływ ze źródła uchodzi przez zawór (komora przestaje się napełniać).</p>
</html>"));
end ReliefValveLimit;
