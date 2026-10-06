within FishRobot.Tests;
model PipeInertance "Test: narastanie przepływu po skoku ciśnienia (inertancja + opór laminarny)"
  extends Modelica.Icons.Example;
  import Modelica.Constants.pi;

  parameter Modelica.Units.SI.PressureDifference dp_step = 300 "Skok różnicy ciśnień";
  parameter Modelica.Units.SI.Time t_step = 0.1 "Chwila skoku";

  Modelica.Blocks.Sources.Step step(height=dp_step, offset=1.01325e5, startTime=t_step)
    annotation (Placement(transformation(extent={{-90,-10},{-70,10}})));
  FishRobot.Hydraulics.Reservoir high(use_p_in=true)
    annotation (Placement(transformation(extent={{-50,-10},{-30,10}})));
  FishRobot.Hydraulics.Pipe pipe(zeta=0, useInertance=true)
    annotation (Placement(transformation(extent={{0,-10},{20,10}})));
  FishRobot.Hydraulics.Reservoir low
    annotation (Placement(transformation(extent={{70,-10},{50,10}})));

  // Rozwiązanie analityczne równania L·dQ/dt + R·Q = dp (wzory zapisane niezależnie od Pipe).
  parameter Real R(unit="Pa.s/m3") = 128*pipe.mu*pipe.l/(pi*pipe.d^4) "Opór laminarny";
  parameter Real L(unit="Pa.s2/m3") = pipe.rho*pipe.l/(pi*pipe.d^2/4) "Inertancja";
  parameter Modelica.Units.SI.Time tau = L/R "Stała czasowa";
  Modelica.Units.SI.VolumeFlowRate Q_analytic =
    if time < t_step then 0 else dp_step/R*(1 - exp(-(time - t_step)/tau)) "Q(t) analitycznie";
equation
  connect(step.y, high.p_in) annotation (Line(points={{-69,0},{-54,0}}, color={0,0,127}));
  connect(high.port, pipe.port_a) annotation (Line(points={{-30,0},{0,0}}, color={0,128,255}));
  connect(pipe.port_b, low.port) annotation (Line(points={{20,0},{50,0}}, color={0,128,255}));
  annotation (
    experiment(StopTime=3.0, Interval=0.002, Tolerance=1e-8),
    Documentation(info="<html>
<p>Skok różnicy ciśnień o 300 Pa na końcach rury z inertancją. Przepływ nie może zmienić się skokowo
(słup cieczy ma masę), tylko narasta jak w obwodzie RL:
<code>Q(t) = dp/R·(1 - e<sup>-t/&tau;</sup>)</code>, <code>&tau; = L/R</code> (ok. 0,5 s dla domyślnej rury).
Oczekiwanie: błąd względem rozwiązania analitycznego &lt; 1% wartości ustalonej.</p>
</html>"));
end PipeInertance;
