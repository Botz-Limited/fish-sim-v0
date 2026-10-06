within FishRobot.Hydraulics;
model ReliefValve "Zawór przelewowy z gładką charakterystyką (otwiera się powyżej p_set)"
  extends FishRobot.Interfaces.PartialTwoPort;

  parameter Modelica.Units.SI.PressureDifference p_set = 50e3
    "Ciśnienie otwarcia (różnica port_a - port_b) (PLACEHOLDER – do identyfikacji)";
  parameter Modelica.Units.SI.PressureDifference dp_open = 5e3
    "Nadwyżka ponad p_set, przy której zawór przepuszcza V_flow_nominal (PLACEHOLDER – do identyfikacji)";
  parameter Modelica.Units.SI.VolumeFlowRate V_flow_nominal = 2e-5
    "Przepływ nominalny przy p_set + dp_open (PLACEHOLDER – do identyfikacji)";
  parameter Real G_leak(unit="m3/(s.Pa)") = 1e-12
    "Przewodność przecieku zamkniętego zaworu (PLACEHOLDER – do identyfikacji)";
  parameter Modelica.Units.SI.PressureDifference dp_smooth = 500
    "Szerokość wygładzenia charakterystyki wokół p_set";

  final parameter Real G_open(unit="m3/(s.Pa)") = V_flow_nominal/dp_open "Przewodność otwartego zaworu";

  Modelica.Units.SI.PressureDifference dp_over "Wygładzona nadwyżka ciśnienia ponad p_set (>= 0)";
  Modelica.Units.SI.Power P_loss "Moc rozpraszana w zaworze";

equation
  // Gładka rampa max(0, x) ≈ (x + sqrt(x² + dp_smooth²))/2: bez przełączania, bez zdarzeń.
  dp_over = ((dp - p_set) + sqrt((dp - p_set)^2 + dp_smooth^2))/2;
  V_flow = G_leak*dp + G_open*dp_over;
  P_loss = dp*V_flow;

  annotation (
    Icon(graphics={
      Polygon(points={{-60,40},{-60,-40},{0,0},{-60,40}}, lineColor={0,0,0}, fillColor={255,255,255},
        fillPattern=FillPattern.Solid),
      Polygon(points={{60,40},{60,-40},{0,0},{60,40}}, lineColor={0,0,0}, fillColor={255,255,255},
        fillPattern=FillPattern.Solid),
      Line(points={{-90,0},{-60,0}}, color={0,128,255}),
      Line(points={{60,0},{90,0}}, color={0,128,255}),
      Line(points={{0,0},{0,60},{-20,70},{20,80},{-20,90},{20,100}}, color={0,0,0}),
      Text(extent={{-150,-50},{150,-90}}, textString="%name", textColor={0,0,255})}),
    Documentation(info="<html>
<p>Zawór przelewowy chroni komory przed rozerwaniem: gdy różnica ciśnień przekroczy <code>p_set</code>,
zawór się otwiera i upuszcza ciecz z <code>port_a</code> do <code>port_b</code>. Działa tylko w jedną stronę;
dla ochrony obu komór użyj dwóch zaworów połączonych przeciwsobnie.</p>
<pre>  V_flow = G_leak·dp + G_open·smax(dp - p_set)
  smax(x) = (x + sqrt(x² + dp_smooth²))/2   ≈ max(0, x)
  G_open = V_flow_nominal / dp_open</pre>
<p><b>Parametry jak z karty katalogowej:</b> zawór zaczyna się otwierać przy <code>p_set</code>, a przy
<code>p_set + dp_open</code> przepuszcza <code>V_flow_nominal</code>. Dopóki przepływ nie przekracza
nominalnego, ciśnienie nie przekroczy <code>p_set + dp_open</code> – to jest „tolerancja charakterystyki”.</p>
<p><b>Dlaczego gładko:</b> twarde <code>if dp &gt; p_set</code> generuje zdarzenie przy każdym otwarciu i zamknięciu.
Przy ogonie machającym kilka razy na sekundę solver musiałby się co chwilę restartować, a w pobliżu progu
mogłoby dojść do „drgania” (chattering). Cena wygładzenia: zawór przepuszcza odrobinę już tuż poniżej
<code>p_set</code> (przy <code>dp = p_set</code> przepływ to <code>G_open·dp_smooth/2</code>).</p>
<p><b>Energia:</b> cała moc <code>dp·V_flow</code> zamienia się w ciepło – zawór jest czystą stratą,
którą zobaczysz w bilansie energii (scenariusz <code>ReliefValveDemo</code>).</p>
</html>"));
end ReliefValve;
