within FishRobot.Tests;
model PipeTurbulentVsMSL "Test: tarcie w rurze od laminarnego do turbulentnego vs Modelica.Fluid.Pipes.StaticPipe"
  extends Modelica.Icons.Example;
  package Medium = Modelica.Media.Water.ConstantPropertyLiquidWater "Woda o stałych właściwościach";

  parameter Modelica.Units.SI.VolumeFlowRate Q_max = 4e-5 "Przepływ końcowy (Re ok. 12 700)";
  parameter Modelica.Units.SI.Length l = 0.2 "Długość przewodu";
  parameter Modelica.Units.SI.Diameter d = 4e-3 "Średnica wewnętrzna";
  parameter Modelica.Units.SI.Length roughness = 2.5e-5 "Chropowatość ścianki";

  inner Modelica.Fluid.System system
    annotation (Placement(transformation(extent={{60,40},{80,60}})));
  Modelica.Blocks.Sources.Ramp ramp(height=Q_max, duration=1, startTime=0) "Przepływ objętościowy"
    annotation (Placement(transformation(extent={{-90,-10},{-70,10}})));

  // --- Własny pakiet (gęstość i lepkość jak w medium MSL, żeby porównywać tylko modele tarcia)
  FishRobot.Hydraulics.VolumeFlowSource source
    annotation (Placement(transformation(extent={{-50,10},{-30,30}})));
  FishRobot.Hydraulics.Pipe pipe(l=l, d=d, roughness=roughness, zeta=0, rho=Medium.d_const, mu=Medium.eta_const)
    annotation (Placement(transformation(extent={{0,10},{20,30}})));
  FishRobot.Hydraulics.Reservoir sink
    annotation (Placement(transformation(extent={{70,10},{50,30}})));

  // --- Modelica.Fluid: ten sam przepływ masowy przez StaticPipe z DetailedPipeFlow
  Modelica.Blocks.Math.Gain toMass(k=Medium.d_const) "m_flow = rho·Q"
    annotation (Placement(transformation(extent={{-60,-40},{-50,-30}})));
  Modelica.Fluid.Sources.MassFlowSource_T fluidSource(redeclare package Medium = Medium,
    use_m_flow_in=true, nPorts=1)
    annotation (Placement(transformation(extent={{-40,-50},{-20,-30}})));
  Modelica.Fluid.Pipes.StaticPipe fluidPipe(redeclare package Medium = Medium,
    length=l, diameter=d, roughness=roughness,
    redeclare model FlowModel = Modelica.Fluid.Pipes.BaseClasses.FlowModels.DetailedPipeFlow)
    annotation (Placement(transformation(extent={{0,-50},{20,-30}})));
  Modelica.Fluid.Sources.Boundary_pT fluidSink(redeclare package Medium = Medium, nPorts=1)
    annotation (Placement(transformation(extent={{70,-50},{50,-30}})));

  Modelica.Units.SI.PressureDifference dp_msl = fluidPipe.port_a.p - fluidPipe.port_b.p
    "Spadek ciśnienia w StaticPipe";
equation
  connect(ramp.y, source.V_flow) annotation (Line(points={{-69,0},{-60,0},{-60,20},{-54,20}}, color={0,0,127}));
  connect(source.port, pipe.port_a) annotation (Line(points={{-30,20},{0,20}}, color={0,128,255}));
  connect(pipe.port_b, sink.port) annotation (Line(points={{20,20},{50,20}}, color={0,128,255}));
  connect(ramp.y, toMass.u) annotation (Line(points={{-69,0},{-66,0},{-66,-35},{-61,-35}}, color={0,0,127}));
  connect(toMass.y, fluidSource.m_flow_in) annotation (Line(points={{-49.5,-35},{-46,-35},{-46,-32},{-40,-32}}, color={0,0,127}));
  connect(fluidSource.ports[1], fluidPipe.port_a) annotation (Line(points={{-20,-40},{0,-40}}, color={0,127,255}));
  connect(fluidPipe.port_b, fluidSink.ports[1]) annotation (Line(points={{20,-40},{50,-40}}, color={0,127,255}));
  annotation (
    experiment(StopTime=1.0, Interval=0.001, Tolerance=1e-8),
    Documentation(info="<html>
<p>Ten sam rosnący przepływ płynie przez <code>Hydraulics.Pipe</code> (bez strat miejscowych) i przez
<code>Modelica.Fluid.Pipes.StaticPipe</code> z modelem <code>DetailedPipeFlow</code>. To dwie niezależne
implementacje tarcia, więc ich zgodność jest testem.</p>
<p>Oczekiwanie: dla Re &lt; 1500 oba dają Hagena–Poiseuille’a (różnica &lt; 1%), dla Re &gt; 4000 oba liczą
tarcie turbulentne z chropowatością (Haaland vs Colebrook, różnica &lt; 3%). W zakresie przejściowym każdy model
interpoluje inaczej: MSL zaczyna przejście przy Re &asymp; 1600 (granica zależy od chropowatości), a
<code>Hydraulics.Pipe</code> przy 2000. Tam dopuszczamy różnicę do 10%. Przejście w rzeczywistej rurze i tak
zależy od zaburzeń na wlocie, więc żaden z tych modeli nie jest tu „dokładny”.</p>
</html>"));
end PipeTurbulentVsMSL;
