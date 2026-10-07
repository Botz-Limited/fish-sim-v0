within FishRobot.HydraulicsFluid;
model GearPump "Pompa zębata (wyporowa) na złączach Modelica.Fluid – te same równania co Hydraulics.GearPump"
  extends Modelica.Fluid.Interfaces.PartialTwoPortTransport(
    final show_V_flow=false, final show_T=false);
  import Modelica.Constants.pi;

  parameter Modelica.Units.SI.Volume D_rev = 3e-7
    "Wydajność geometryczna na obrót (0,3 ml/obr) (PLACEHOLDER – do identyfikacji)";
  parameter Real k_leak(unit="m3/(s.Pa)") = 2e-11
    "Współczynnik przecieku wewnętrznego (PLACEHOLDER – do identyfikacji)";
  parameter Real eta_m(min=0.1, max=1) = 0.8 "Sprawność mechaniczna (PLACEHOLDER – do identyfikacji)";
  parameter Modelica.Units.SI.AngularVelocity w_small = 1
    "Próg regularyzacji kierunku obrotów w momencie tarcia";
  parameter Modelica.Units.SI.Density rho = Medium.density_pTX(Medium.p_default, Medium.T_default, Medium.X_default)
    "Gęstość cieczy (medium nieściśliwe: stała)";

  final parameter Real D(unit="m3/rad") = D_rev/(2*pi) "Wydajność na radian";

  Modelica.Mechanics.Rotational.Interfaces.Flange_a flange "Wał pompy"
    annotation (Placement(transformation(extent={{-10,90},{10,110}})));

  Modelica.Units.SI.AngularVelocity w "Prędkość obrotowa wału";
  Modelica.Units.SI.VolumeFlowRate Q(nominal=1e-5) "Przepływ objętościowy port_a -> port_b";
  Modelica.Units.SI.PressureDifference dp_pump(nominal=1e4) "Przyrost ciśnienia port_b - port_a";
  Modelica.Units.SI.Torque tau_fric "Moment tarcia (zawsze przeciwny do obrotów)";

equation
  w = der(flange.phi);
  dp_pump = -dp;
  // Te same równania co w Hydraulics.GearPump; złącze Fluid przenosi masę, więc m_flow = rho·Q.
  Q = D*w - k_leak*dp_pump;
  m_flow = rho*Q;
  tau_fric = D*abs(dp_pump)*(1/eta_m - 1)*w/sqrt(w^2 + w_small^2);
  flange.tau = D*dp_pump + tau_fric;
  // Zmienne strumieniowe: entalpia przechodzi bez zmian (model izotermiczny; nagrzewanie cieczy
  // pracą pompy to ułamki kelwina, pomijamy je jak zawory w Modelica.Fluid.Valves).
  port_a.h_outflow = inStream(port_b.h_outflow);
  port_b.h_outflow = inStream(port_a.h_outflow);

  annotation (
    Icon(coordinateSystem(extent={{-100,-100},{100,100}}), graphics={
      Ellipse(extent={{-80,80},{80,-80}}, lineColor={0,0,0}, fillColor={255,255,255},
        fillPattern=FillPattern.Solid),
      Ellipse(extent={{-45,45},{5,-5}}, lineColor={0,0,0}, fillColor={175,175,175},
        fillPattern=FillPattern.Solid),
      Ellipse(extent={{-5,5},{45,-45}}, lineColor={0,0,0}, fillColor={175,175,175},
        fillPattern=FillPattern.Solid),
      Line(points={{-100,0},{-80,0}}, color={0,127,255}),
      Line(points={{80,0},{100,0}}, color={0,127,255}),
      Line(points={{0,80},{0,100}}),
      Text(extent={{-150,-90},{150,-130}}, textString="%name", textColor={0,0,255})}),
    Documentation(info="<html>
<p>Modelica.Fluid ma tylko <b>pompy wirowe</b> (<code>Machines.PrescribedPump</code>, <code>Machines.Pump</code>),
opisane krzywą wysokości podnoszenia <i>H(V_flow, n)</i>. Pompa zębata jest wyporowa: przepływ zależy prawie
wyłącznie od obrotów, więc trzeba ją dopisać. Bazą jest <code>PartialTwoPortTransport</code>
(element bez magazynowania masy i energii), który daje <code>dp = port_a.p - port_b.p</code>,
<code>m_flow = port_a.m_flow</code> i bilans masy. Do dopisania zostają:</p>
<pre>  Q      = D·&omega; - k_leak·&Delta;p        (&Delta;p = p_b - p_a)
  m_flow = &rho;·Q
  &tau;      = D·&Delta;p + &tau;_fric
  h_outflow: bez zmian (izotermicznie)</pre>
<p>Porównaj z <code>Hydraulics.GearPump</code>: fizyka ta sama, ale tu trzeba jeszcze zadbać o gęstość
i o zmienne strumieniowe (entalpia, skład), których w lekkim pakiecie nie ma wcale.</p>
</html>"));
end GearPump;
