within FishRobot.Tests;
model PipeLaminar "Test: spadek ciśnienia w rurze vs prawo Hagena–Poiseuille’a"
  extends Modelica.Icons.Example;
  import Modelica.Constants.pi;

  parameter Modelica.Units.SI.VolumeFlowRate Q_max = 2e-6 "Przepływ końcowy (Re ok. 640 – zakres laminarny)";

  Modelica.Blocks.Sources.Ramp ramp(height=Q_max, duration=1, startTime=0)
    annotation (Placement(transformation(extent={{-90,-10},{-70,10}})));
  FishRobot.Hydraulics.VolumeFlowSource source
    annotation (Placement(transformation(extent={{-50,-10},{-30,10}})));
  FishRobot.Hydraulics.Pipe pipe(zeta=0)
    annotation (Placement(transformation(extent={{0,-10},{20,10}})));
  FishRobot.Hydraulics.Reservoir sink
    annotation (Placement(transformation(extent={{70,-10},{50,10}})));

  // Wzór analityczny zapisany niezależnie od kodu Pipe (żeby test faktycznie coś sprawdzał).
  Modelica.Units.SI.PressureDifference dp_analytic = 128*pipe.mu*pipe.l*pipe.V_flow/(pi*pipe.d^4)
    "Hagen–Poiseuille: dp = 128·mu·l·Q / (pi·d^4)";
equation
  connect(ramp.y, source.V_flow) annotation (Line(points={{-69,0},{-54,0}}, color={0,0,127}));
  connect(source.port, pipe.port_a) annotation (Line(points={{-30,0},{0,0}}, color={0,128,255}));
  connect(pipe.port_b, sink.port) annotation (Line(points={{20,0},{50,0}}, color={0,128,255}));
  annotation (
    experiment(StopTime=1.0, Interval=0.01, Tolerance=1e-8),
    Documentation(info="<html>
<p>Źródło wymusza rosnący przepływ przez rurę bez strat miejscowych (<code>zeta = 0</code>).
Oczekiwanie: <code>pipe.dp</code> rośnie liniowo z przepływem i pokrywa się z <code>dp_analytic</code>
(błąd &lt; 1%). Dla <code>d = 4 mm</code>, <code>l = 0,2 m</code> i <code>Q = 2 ml/s</code> to ok. 64 Pa.</p>
</html>"));
end PipeLaminar;
