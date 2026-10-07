within FishRobot.Tests;
model PipeQuadratic "Test: człon kwadratowy i regularyzacja przy przepływie zmieniającym kierunek"
  extends Modelica.Icons.Example;

  Modelica.Blocks.Sources.Sine sine(amplitude=2e-5, f=1)
    annotation (Placement(transformation(extent={{-90,-10},{-70,10}})));
  FishRobot.Hydraulics.VolumeFlowSource source
    annotation (Placement(transformation(extent={{-50,-10},{-30,10}})));
  FishRobot.Hydraulics.Pipe pipe(zeta=1.5, useTurbulent=false)
    "Bez przejścia w turbulencję: test dotyczy tylko członu kwadratowego i jego regularyzacji w zerze"
    annotation (Placement(transformation(extent={{0,-10},{20,10}})));
  FishRobot.Hydraulics.Reservoir sink
    annotation (Placement(transformation(extent={{70,-10},{50,10}})));

  // Wzór bez regularyzacji: R_lam·Q + R_local·|Q|·Q.
  Modelica.Units.SI.PressureDifference dp_exact =
    pipe.R_lam*pipe.V_flow + pipe.R_local*abs(pipe.V_flow)*pipe.V_flow "Charakterystyka bez regularyzacji";
equation
  connect(sine.y, source.V_flow) annotation (Line(points={{-69,0},{-54,0}}, color={0,0,127}));
  connect(source.port, pipe.port_a) annotation (Line(points={{-30,0},{0,0}}, color={0,128,255}));
  connect(pipe.port_b, sink.port) annotation (Line(points={{20,0},{50,0}}, color={0,128,255}));
  annotation (
    experiment(StopTime=2.0, Interval=0.002, Tolerance=1e-8),
    Documentation(info="<html>
<p>Przepływ sinusoidalny ±20 ml/s, 1 Hz – zmienia kierunek dwa razy na okres, tak jak w ogonie ryby.
Oczekiwanie: <code>pipe.dp</code> zgodne z <code>dp_exact</code> (&lt; 1%) wszędzie tam, gdzie
<code>|Q| &gt; 100·V_flow_small</code>, a symulacja przechodzi przez zero bez zdarzeń (gładka charakterystyka).</p>
</html>"));
end PipeQuadratic;
