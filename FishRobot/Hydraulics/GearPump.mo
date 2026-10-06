within FishRobot.Hydraulics;
model GearPump "Odwracalna pompa zębata (wyporowa) z przeciekiem i tarciem mechanicznym"
  extends FishRobot.Interfaces.PartialTwoPort;
  import Modelica.Constants.pi;

  parameter Modelica.Units.SI.Volume D_rev = 3e-7
    "Wydajność geometryczna na obrót (0,3 ml/obr) (PLACEHOLDER – do identyfikacji)";
  parameter Real k_leak(unit="m3/(s.Pa)") = 2e-11
    "Współczynnik przecieku wewnętrznego (PLACEHOLDER – do identyfikacji)";
  parameter Real eta_m(min=0.1, max=1) = 0.8 "Sprawność mechaniczna (PLACEHOLDER – do identyfikacji)";
  parameter Modelica.Units.SI.AngularVelocity w_small = 1
    "Próg regularyzacji kierunku obrotów w momencie tarcia";

  final parameter Real D(unit="m3/rad") = D_rev/(2*pi) "Wydajność na radian";

  Modelica.Mechanics.Rotational.Interfaces.Flange_a flange "Wał pompy"
    annotation (Placement(transformation(extent={{-10,90},{10,110}})));

  Modelica.Units.SI.AngularVelocity w "Prędkość obrotowa wału";
  Modelica.Units.SI.PressureDifference dp_pump "Przyrost ciśnienia port_b - port_a";
  Modelica.Units.SI.Torque tau_fric "Moment tarcia (zawsze przeciwny do obrotów)";
  Modelica.Units.SI.Power P_shaft "Moc mechaniczna na wale (dodatnia = pompa pobiera)";
  Modelica.Units.SI.Power P_hyd "Moc hydrauliczna oddana cieczy";
  Modelica.Units.SI.Power P_loss_leak "Straty przecieku k_leak·dp²";
  Modelica.Units.SI.Power P_loss_mech "Straty tarcia mechanicznego";

equation
  w = der(flange.phi);
  dp_pump = -dp;
  // Przepływ: idealne wyparcie minus przeciek wsteczny pod ciśnieniem.
  V_flow = D*w - k_leak*dp_pump;
  // Tarcie proporcjonalne do ciśnienia (docisk zębów i łożysk), znak jak prędkość (gładko).
  tau_fric = D*abs(dp_pump)*(1/eta_m - 1)*w/sqrt(w^2 + w_small^2);
  flange.tau = D*dp_pump + tau_fric;
  P_shaft = flange.tau*w;
  P_hyd = dp_pump*V_flow;
  P_loss_leak = k_leak*dp_pump^2;
  P_loss_mech = tau_fric*w;

  annotation (
    Icon(graphics={
      Ellipse(extent={{-80,80},{80,-80}}, lineColor={0,0,0}, fillColor={255,255,255},
        fillPattern=FillPattern.Solid),
      Ellipse(extent={{-45,45},{5,-5}}, lineColor={0,0,0}, fillColor={175,175,175},
        fillPattern=FillPattern.Solid),
      Ellipse(extent={{-5,5},{45,-45}}, lineColor={0,0,0}, fillColor={175,175,175},
        fillPattern=FillPattern.Solid),
      Polygon(points={{50,60},{70,40},{40,40},{50,60}}, lineColor={0,128,255}, fillColor={0,128,255},
        fillPattern=FillPattern.Solid),
      Line(points={{-90,0},{-80,0}}, color={0,128,255}),
      Line(points={{80,0},{90,0}}, color={0,128,255}),
      Line(points={{0,80},{0,90}}),
      Text(extent={{-150,-90},{150,-130}}, textString="%name", textColor={0,0,255})}),
    Documentation(info="<html>
<p>Pompa wyporowa: każdy obrót wału przenosi stałą objętość <code>D_rev</code> z <code>port_a</code> do
<code>port_b</code>. Przy dodatnich obrotach ciecz płynie a &rarr; b, przy ujemnych odwrotnie.</p>
<pre>  V_flow = D·&omega; - k_leak·&Delta;p           (&Delta;p = p_b - p_a)
  &tau;      = D·&Delta;p + &tau;_fric
  &tau;_fric = D·|&Delta;p|·(1/&eta;_m - 1)·sgn(&omega;)</pre>
<p><b>Przeciek</b> <code>k_leak·&Delta;p</code>: ciecz cofa się przez luzy między zębami a obudową.
Im wyższe ciśnienie, tym mniej cieczy pompa faktycznie dostarcza.</p>
<p><b>Sprawność mechaniczna:</b> w trybie pompy (<code>&Delta;p·&omega; &gt; 0</code>) moment wynosi dokładnie
<code>D·&Delta;p/&eta;_m</code>. Tarcie zapisano jako osobny moment <b>zawsze przeciwny do obrotów</b>, a nie przez
dzielenie przez <code>&eta;_m</code>. Gdy ciśnienie z komór napędza pompę wstecz (tryb silnika hydraulicznego),
wzór <code>D·&Delta;p/&eta;_m</code> dawałby ujemne straty, czyli tworzyłby energię z niczego.
W tej postaci <code>P_loss_mech = &tau;_fric·&omega; &ge; 0</code> zawsze, więc bilans energii się zamyka.</p>
<p><b>Bilans mocy pompy:</b> <code>P_shaft = P_hyd + P_loss_leak + P_loss_mech</code>.</p>
<p>Funkcja <code>sgn(&omega;)</code> jest wygładzona (<code>&omega;/sqrt(&omega;<sup>2</sup>+&omega;_small<sup>2</sup>)</code>),
żeby nie było zdarzeń przy zmianie kierunku obrotów.</p>
</html>"));
end GearPump;
