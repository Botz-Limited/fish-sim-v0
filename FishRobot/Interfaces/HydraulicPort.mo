within FishRobot.Interfaces;
connector HydraulicPort "Złącze hydrauliczne: ciśnienie (potencjał) i przepływ objętościowy (flow)"
  // nominal: typowy rząd wielkości – solver skaluje nim tolerancje i iteracje Newtona.
  // Bez tego przepływ rzędu 1e-5 m3/s byłby traktowany jak wielkość rzędu 1.
  Modelica.Units.SI.AbsolutePressure p(start=1.01325e5, nominal=1e5) "Ciśnienie w punkcie połączenia";
  flow Modelica.Units.SI.VolumeFlowRate V_flow(nominal=1e-5) "Przepływ objętościowy DO komponentu przez ten port";
  annotation (Documentation(info="<html>
<p>Złącze akauzalne dla nieściśliwej cieczy. W węźle, gdzie łączy się kilka portów, Modelica generuje:</p>
<ul>
<li>równość potencjałów: <code>p</code> jest takie samo we wszystkich portach węzła,</li>
<li>sumę przepływów równą zero: <code>&Sigma; V_flow = 0</code> (zachowanie objętości – odpowiednik prawa Kirchhoffa).</li>
</ul>
<p>Para <code>(p, V_flow)</code> jest dobrana tak, że <code>p·V_flow</code> to moc [W] wpływająca do komponentu.
Dzięki temu energia przepływa przez połączenia tak samo jak w obwodzie elektrycznym (<code>v·i</code>)
lub mechanicznym (<code>&tau;·&omega;</code>).</p>
</html>"));
end HydraulicPort;
