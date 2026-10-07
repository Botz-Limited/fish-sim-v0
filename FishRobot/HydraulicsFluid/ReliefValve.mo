within FishRobot.HydraulicsFluid;
model ReliefValve "Zawór przelewowy złożony z Valves.ValveLinear i czujnika różnicy ciśnień (linia sterująca)"
  extends Modelica.Fluid.Interfaces.PartialTwoPort;

  parameter Modelica.Units.SI.PressureDifference p_set = 50e3
    "Ciśnienie otwarcia (różnica port_a - port_b) (PLACEHOLDER – do identyfikacji)";
  parameter Modelica.Units.SI.PressureDifference dp_open = 5e3
    "Nadwyżka ponad p_set, przy której zawór jest w pełni otwarty (PLACEHOLDER – do identyfikacji)";
  parameter Modelica.Units.SI.VolumeFlowRate V_flow_nominal = 2e-5
    "Przepływ przy pełnym otwarciu i dp = p_set + dp_open (PLACEHOLDER – do identyfikacji)";
  parameter Real opening_leak = 2.75e-3
    "Otwarcie zamkniętego zaworu (przeciek; odpowiada G_leak = 1e-12 m3/(s·Pa) z Hydraulics.ReliefValve)";
  parameter Modelica.Units.SI.PressureDifference dp_smooth = 500
    "Szerokość wygładzenia charakterystyki wokół p_set";
  parameter Modelica.Units.SI.Density rho = Medium.density_pTX(Medium.p_default, Medium.T_default, Medium.X_default)
    "Gęstość cieczy (do przeliczenia przepływu nominalnego na masowy)";

  Modelica.Fluid.Valves.ValveLinear valve(
    redeclare package Medium = Medium,
    final allowFlowReversal=allowFlowReversal,
    final dp_nominal=p_set + dp_open,
    final m_flow_nominal=rho*V_flow_nominal) "Zawór o przepływie m_flow = opening·k·dp"
    annotation (Placement(transformation(extent={{-10,-10},{10,10}})));
  Modelica.Fluid.Sensors.RelativePressure dpSensor(redeclare package Medium = Medium)
    "Linia sterująca: różnica ciśnień port_a - port_b działa na grzybek zaworu"
    annotation (Placement(transformation(extent={{-10,50},{10,30}})));

equation
  // Grzybek otwiera się proporcjonalnie do nadwyżki ciśnienia ponad p_set (gładkie max(0, x)).
  // Bez ograniczenia do 1: przy przepływie ponad nominalny zawór otwiera się dalej, jak w Hydraulics.ReliefValve.
  valve.opening = opening_leak
    + ((dpSensor.p_rel - p_set) + sqrt((dpSensor.p_rel - p_set)^2 + dp_smooth^2))/2/dp_open;
  connect(port_a, valve.port_a) annotation (Line(points={{-100,0},{-10,0}}, color={0,127,255}));
  connect(valve.port_b, port_b) annotation (Line(points={{10,0},{100,0}}, color={0,127,255}));
  connect(dpSensor.port_a, port_a) annotation (Line(points={{-10,40},{-60,40},{-60,0},{-100,0}}, color={0,127,255}));
  connect(dpSensor.port_b, port_b) annotation (Line(points={{10,40},{60,40},{60,0},{100,0}}, color={0,127,255}));

  annotation (
    Icon(coordinateSystem(extent={{-100,-100},{100,100}}), graphics={
      Polygon(points={{-60,40},{-60,-40},{0,0},{-60,40}}, lineColor={0,0,0}, fillColor={255,255,255},
        fillPattern=FillPattern.Solid),
      Polygon(points={{60,40},{60,-40},{0,0},{60,40}}, lineColor={0,0,0}, fillColor={255,255,255},
        fillPattern=FillPattern.Solid),
      Line(points={{-100,0},{-60,0}}, color={0,127,255}),
      Line(points={{60,0},{100,0}}, color={0,127,255}),
      Line(points={{-80,0},{-80,60},{0,60},{0,0}}, color={0,127,255}, pattern=LinePattern.Dash),
      Text(extent={{-150,-50},{150,-90}}, textString="%name", textColor={0,0,255})}),
    Documentation(info="<html>
<p>W Modelica.Fluid nie ma zaworu przelewowego. Składamy go jak na schemacie hydraulicznym:
zawór (<code>Valves.ValveLinear</code>, <code>m_flow = opening·k·dp</code>) i linia sterująca
(<code>Sensors.RelativePressure</code>), która otwiera grzybek proporcjonalnie do nadwyżki ciśnienia:</p>
<pre>  opening = opening_leak + smax(dp - p_set)/dp_open
  m_flow  = opening · &rho;·V_flow_nominal/(p_set + dp_open) · dp</pre>
<p><b>Różnica względem <code>Hydraulics.ReliefValve</code>:</b> tam przepływ jest proporcjonalny do samej nadwyżki
(<code>G_open·smax(dp - p_set)</code>), a tu do nadwyżki razy <code>dp/(p_set + dp_open)</code>.
W zakresie pracy zaworu (<code>dp</code> od <code>p_set</code> do <code>p_set + dp_open</code>) ten czynnik wynosi
0,91–1, więc charakterystyki różnią się o kilka procent. Przy <code>p_set + dp_open</code> obie dają
<code>V_flow_nominal</code>.</p>
</html>"));
end ReliefValve;
