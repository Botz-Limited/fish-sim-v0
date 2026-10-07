within FishRobot.Calibration;
model LinearThrottle "Zawór dławiący o liniowej charakterystyce V_flow = G·dp (ustawia tylko punkt pracy)"
  extends FishRobot.Interfaces.PartialTwoPort;
  parameter Real G(unit="m3/(s.Pa)") = 1e-9 "Przewodność (nastawa iglicy)";
equation
  V_flow = G*dp;
  annotation (Icon(graphics={
    Polygon(points={{-80,40},{0,0},{-80,-40},{-80,40}}, lineColor={0,128,255}, fillColor={255,255,255},
      fillPattern=FillPattern.Solid),
    Polygon(points={{80,40},{0,0},{80,-40},{80,40}}, lineColor={0,128,255}, fillColor={255,255,255},
      fillPattern=FillPattern.Solid),
    Line(points={{0,0},{0,60}}),
    Line(points={{-20,60},{20,60}}),
    Text(extent={{-150,-50},{150,-90}}, textString="%name", textColor={0,0,255})}),
    Documentation(info="<html>
<p>Charakterystyka prawdziwego zaworu iglicowego jest bliższa kwadratowej, ale w kroku 3 zawór tylko
ustawia ciśnienie na wylocie pompy. Identyfikacja korzysta z mierzonych &Delta;p i Q, a nie z modelu zaworu.</p>
</html>"));
end LinearThrottle;
