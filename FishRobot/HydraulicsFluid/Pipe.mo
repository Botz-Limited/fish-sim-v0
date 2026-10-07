within FishRobot.HydraulicsFluid;
model Pipe "Przewód z Modelica.Fluid: StaticPipe (tarcie o ścianki) + SimpleGenericOrifice (straty miejscowe)"
  extends Modelica.Fluid.Interfaces.PartialTwoPort;

  parameter Modelica.Units.SI.Length l = 0.2 "Długość przewodu (PLACEHOLDER – do identyfikacji)";
  parameter Modelica.Units.SI.Diameter d = 4e-3 "Średnica wewnętrzna (PLACEHOLDER – do identyfikacji)";
  parameter Real zeta(min=0) = 1.5 "Współczynnik strat miejscowych (kolana, złączki) (PLACEHOLDER – do identyfikacji)";

  Modelica.Fluid.Pipes.StaticPipe pipe(
    redeclare package Medium = Medium,
    final allowFlowReversal=allowFlowReversal,
    length=l,
    diameter=d,
    redeclare model FlowModel = Modelica.Fluid.Pipes.BaseClasses.FlowModels.DetailedPipeFlow)
    "Tarcie o ścianki: laminarne (Hagen–Poiseuille) dla Re < 2000, przejściowe, turbulentne (Colebrook)"
    annotation (Placement(transformation(extent={{-50,-10},{-30,10}})));
  Modelica.Fluid.Fittings.SimpleGenericOrifice fittings(
    redeclare package Medium = Medium,
    final allowFlowReversal=allowFlowReversal,
    diameter=d,
    zeta=zeta) "Straty miejscowe dp = zeta·rho·v²/2"
    annotation (Placement(transformation(extent={{30,-10},{50,10}})));

  Modelica.Units.SI.PressureDifference dp(nominal=1e3) = port_a.p - port_b.p "Spadek ciśnienia na przewodzie";
  Real Re = abs(port_a.m_flow)*4/(Modelica.Constants.pi*d*mu)
    "Liczba Reynoldsa (do porównania z Hydraulics.Pipe.Re)";
protected
  parameter Modelica.Units.SI.DynamicViscosity mu = Medium.dynamicViscosity(
    Medium.setState_pTX(Medium.p_default, Medium.T_default, Medium.X_default)) "Lepkość cieczy";

equation
  connect(port_a, pipe.port_a) annotation (Line(points={{-100,0},{-50,0}}, color={0,127,255}));
  connect(pipe.port_b, fittings.port_a) annotation (Line(points={{-30,0},{30,0}}, color={0,127,255}));
  connect(fittings.port_b, port_b) annotation (Line(points={{50,0},{100,0}}, color={0,127,255}));

  annotation (
    Icon(coordinateSystem(extent={{-100,-100},{100,100}}), graphics={
      Rectangle(extent={{-90,20},{90,-20}}, lineColor={0,0,0}, fillColor={0,127,255},
        fillPattern=FillPattern.HorizontalCylinder),
      Text(extent={{-150,70},{150,30}}, textString="%name", textColor={0,0,255})}),
    Documentation(info="<html>
<p>Ten komponent da się złożyć w całości z biblioteki: <code>Pipes.StaticPipe</code> liczy tarcie o ścianki,
a <code>Fittings.SimpleGenericOrifice</code> straty miejscowe <code>&zeta;·&rho;·v<sup>2</sup>/2</code>.</p>
<p><b>Różnica względem <code>Hydraulics.Pipe</code>:</b> tam tarcie jest zawsze laminarne (Hagen–Poiseuille).
Tu <code>DetailedPipeFlow</code> dla Re &lt; 2000 daje to samo, powyżej Re = 4000 przechodzi w opór turbulentny
z uwzględnieniem chropowatości ścianki (Colebrook), a pomiędzy interpoluje. Przy szybkim pompowaniu
w scenariuszu <code>HydraulicsMSLFluid</code> <code>Re</code> dochodzi do ok. 5200, więc przepływ jest już turbulentny,
a spadek ciśnienia wychodzi ok. 1,7 raza większy niż w <code>Hydraulics.Pipe</code>.</p>
</html>"));
end Pipe;
