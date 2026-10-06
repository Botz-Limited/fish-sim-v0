within FishRobot.Tail;
model QuadraticDamper "Tłumienie hydrodynamiczne c_h·|w|·w (regularyzowane), odniesione do podłoża"
  parameter Real c_h(unit="N.m.s2/rad2") = 1e-2 "Współczynnik tłumienia kwadratowego (PLACEHOLDER – do identyfikacji)";
  parameter Modelica.Units.SI.AngularVelocity w_small = 1e-2 "Próg regularyzacji |w|";
  Modelica.Mechanics.Rotational.Interfaces.Flange_a flange
    annotation (Placement(transformation(extent={{-110,-10},{-90,10}})));
  Modelica.Units.SI.AngularVelocity w "Prędkość kątowa";
  Modelica.Units.SI.Power lossPower "Moc oddana wodzie (zawsze >= 0)";
equation
  w = der(flange.phi);
  // w·sqrt(w² + w_small²) zamiast |w|·w: gładko w zerze, bez zdarzeń przy zmianie kierunku machnięcia.
  flange.tau = c_h*w*sqrt(w^2 + w_small^2);
  lossPower = flange.tau*w;
  annotation (
    Icon(graphics={
      Line(points={{-90,0},{-40,0}}),
      Rectangle(extent={{-40,30},{40,-30}}, lineColor={0,0,0}, fillColor={170,213,255},
        fillPattern=FillPattern.Solid),
      Line(points={{-60,30},{-60,-30}}),
      Text(extent={{-40,20},{40,-20}}, textString="w²", textColor={0,0,0}),
      Line(points={{40,-40},{40,-60},{60,-60}}, color={0,0,0}),
      Text(extent={{-150,80},{150,40}}, textString="%name", textColor={0,0,255})}),
    Documentation(info="<html>
<p>Opór wody przy szybkim machnięciu rośnie z kwadratem prędkości (opór ciśnieniowy, jak
<code>&frac12;&rho;C<sub>d</sub>Av<sup>2</sup></code>). Moment <code>&tau; = c_h·|&omega;|·&omega;</code>
działa zawsze przeciwnie do ruchu, więc moc <code>c_h·|&omega;|·&omega;<sup>2</sup></code> jest zawsze rozpraszana.</p>
<p>To jest też część mocy, która w prawdziwej rybie zamienia się w ciąg – w modelu 1 DOF nie da się tego
rozdzielić, dlatego ciąg w <code>SurgeDynamics</code> jest osobnym, empirycznym placeholderem.</p>
</html>"));
end QuadraticDamper;
