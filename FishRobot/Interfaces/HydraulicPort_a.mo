within FishRobot.Interfaces;
connector HydraulicPort_a "Port hydrauliczny (wypełniony) – zwykle wlot"
  extends HydraulicPort;
  annotation (Icon(graphics={Ellipse(extent={{-100,100},{100,-100}}, lineColor={0,128,255},
      fillColor={0,128,255}, fillPattern=FillPattern.Solid, lineThickness=0.5)}),
    Diagram(graphics={Ellipse(extent={{-40,40},{40,-40}}, lineColor={0,128,255},
      fillColor={0,128,255}, fillPattern=FillPattern.Solid)}));
end HydraulicPort_a;
