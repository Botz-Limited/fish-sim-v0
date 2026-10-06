within FishRobot.Hydraulics;
model VolumeFlowSource "Idealne źródło przepływu objętościowego (do testów)"
  FishRobot.Interfaces.HydraulicPort_b port
    annotation (Placement(transformation(extent={{90,-10},{110,10}})));
  Modelica.Blocks.Interfaces.RealInput V_flow(unit="m3/s") "Przepływ wypychany z portu do obwodu"
    annotation (Placement(transformation(extent={{-140,-20},{-100,20}})));
equation
  // Znak minus: V_flow złącza jest dodatni DO komponentu, a źródło wypycha ciecz NA ZEWNĄTRZ.
  port.V_flow = -V_flow;
  annotation (
    Icon(graphics={
      Ellipse(extent={{-60,60},{60,-60}}, lineColor={0,128,255}, fillColor={255,255,255},
        fillPattern=FillPattern.Solid),
      Polygon(points={{-30,30},{40,0},{-30,-30},{-30,30}}, lineColor={0,128,255},
        fillColor={0,128,255}, fillPattern=FillPattern.Solid),
      Line(points={{60,0},{90,0}}, color={0,128,255}),
      Text(extent={{-150,110},{150,70}}, textString="%name", textColor={0,0,255})}),
    Documentation(info="<html>
<p>Wymusza przepływ <code>V_flow</code> wypływający z portu, niezależnie od ciśnienia
(odpowiednik idealnego źródła prądowego). Ciśnienie w porcie wynika z reszty obwodu.
Używane w testach do pomiaru charakterystyki <code>dp(V_flow)</code>.</p>
</html>"));
end VolumeFlowSource;
