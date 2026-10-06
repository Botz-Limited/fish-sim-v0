within FishRobot.Interfaces;
partial model PartialTwoPort "Element dwuportowy bez magazynowania objętości (rura, zawór, ...)"
  HydraulicPort_a port_a "Port a (przepływ dodatni a -> b)"
    annotation (Placement(transformation(extent={{-110,-10},{-90,10}})));
  HydraulicPort_b port_b "Port b"
    annotation (Placement(transformation(extent={{90,-10},{110,10}})));
  Modelica.Units.SI.PressureDifference dp "Spadek ciśnienia dp = port_a.p - port_b.p";
  Modelica.Units.SI.VolumeFlowRate V_flow "Przepływ od port_a do port_b";
equation
  dp = port_a.p - port_b.p;
  V_flow = port_a.V_flow;
  // Ciecz nieściśliwa i brak objętości wewnętrznej: co wpływa przez a, wypływa przez b.
  port_a.V_flow + port_b.V_flow = 0;
  annotation (Documentation(info="<html>
<p>Klasa bazowa dla elementów, które <b>nie przechowują</b> objętości cieczy.
Przepływ wpływający przez <code>port_a</code> równa się przepływowi wypływającemu przez <code>port_b</code>.
Klasy potomne dodają tylko jedno równanie: zależność <code>dp = f(V_flow)</code>.</p>
<p>Moc hydrauliczna pobierana przez element: <code>P = dp·V_flow</code>.</p>
</html>"));
end PartialTwoPort;
