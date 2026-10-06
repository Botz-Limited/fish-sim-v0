within FishRobot.Propulsion;
model SurgeDynamics "Ruch do przodu 1D: (m + m_added_x)·U' = T - ½·ρ·C_d·A·|U|·U"
  parameter Modelica.Units.SI.Mass m = 1.0 "Masa ryby (PLACEHOLDER – do identyfikacji)";
  parameter Modelica.Units.SI.Mass m_added_x = 0.1
    "Masa dodana wzdłuż osi (dla smukłego ciała ok. 5–10% masy) (PLACEHOLDER – do identyfikacji)";
  parameter Real C_d = 0.3 "Współczynnik oporu kadłuba (PLACEHOLDER – do identyfikacji)";
  parameter Modelica.Units.SI.Area A = 0.005 "Pole przekroju poprzecznego kadłuba (PLACEHOLDER – do identyfikacji)";
  parameter Modelica.Units.SI.Density rho = 998.2 "Gęstość wody";
  parameter Modelica.Units.SI.Velocity U_small = 1e-3 "Próg regularyzacji |U|";
  parameter Modelica.Units.SI.Velocity U_start = 0 "Prędkość początkowa";

  Modelica.Blocks.Interfaces.RealInput T(unit="N") "Ciąg"
    annotation (Placement(transformation(extent={{-140,-20},{-100,20}})));
  Modelica.Blocks.Interfaces.RealOutput U(unit="m/s") "Prędkość do przodu"
    annotation (Placement(transformation(extent={{100,30},{120,50}})));
  Modelica.Blocks.Interfaces.RealOutput x(unit="m") "Przebyta droga"
    annotation (Placement(transformation(extent={{100,-50},{120,-30}})));

  Modelica.Units.SI.Force F_drag "Opór kadłuba";
  Modelica.Units.SI.Power P_drag = F_drag*U "Moc rozpraszana przez opór kadłuba (praca użyteczna pływania)";
  Modelica.Units.SI.Energy E_kin = 0.5*(m + m_added_x)*U^2 "Energia kinetyczna (z masą dodaną)";
initial equation
  U = U_start;
  x = 0;
equation
  // U·sqrt(U² + U_small²) zamiast |U|·U: gładko w zerze, bez zdarzeń.
  F_drag = 0.5*rho*C_d*A*U*sqrt(U^2 + U_small^2);
  (m + m_added_x)*der(U) = T - F_drag;
  der(x) = U;
  annotation (
    Icon(graphics={
      Rectangle(extent={{-100,100},{100,-100}}, lineColor={0,0,0}, fillColor={170,213,255},
        fillPattern=FillPattern.Solid),
      Ellipse(extent={{-60,25},{40,-25}}, lineColor={0,0,0}, fillColor={255,170,85},
        fillPattern=FillPattern.Solid),
      Polygon(points={{-60,0},{-85,25},{-85,-25},{-60,0}}, lineColor={0,0,0}, fillColor={255,170,85},
        fillPattern=FillPattern.Solid),
      Line(points={{50,0},{90,0}}, arrow={Arrow.None, Arrow.Filled}),
      Text(extent={{-150,150},{150,110}}, textString="%name", textColor={0,0,255})}),
    Documentation(info="<html>
<p>Ryba jako punkt materialny płynący po prostej:</p>
<pre>  (m + m_added_x)·U' = T - &frac12;·&rho;·C_d·A·|U|·U</pre>
<ul>
<li><code>T</code> – ciąg z płetwy (<code>LighthillFin</code>),</li>
<li><code>m_added_x</code> – masa dodana: rozpędzając się, ryba pcha też wodę przed sobą. Dla smukłego ciała
płynącego wzdłuż osi to tylko kilka procent masy (w pionie i na boki dużo więcej),</li>
<li>opór kadłuba rośnie z kwadratem prędkości. Przy stałym ciągu prędkość ustala się na
<code>U = &radic;(2T/(&rho;·C_d·A))</code>, a czas dochodzenia jest tym krótszy, im większy ciąg.</li>
</ul>
<p>W stanie ustalonym cała moc ciągu <code>T·U</code> idzie w opór kadłuba <code>P_drag</code> – to jest praca
użyteczna pływania. Pominięto: sprzężenie z ruchem pionowym i obrotem (odchylanie kadłuba przy każdym
machnięciu), zmianę oporu od machania ogonem, opór falowy przy powierzchni.</p>
</html>"));
end SurgeDynamics;
