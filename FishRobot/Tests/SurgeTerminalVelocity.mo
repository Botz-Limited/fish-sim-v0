within FishRobot.Tests;
model SurgeTerminalVelocity "Test: ruch do przodu przy stałym ciągu – rozwiązanie analityczne U = U_ss·tanh(t/τ)"
  extends Modelica.Icons.Example;
  parameter Modelica.Units.SI.Force T0 = 0.03 "Stały ciąg";
  final parameter Real k_d(unit="N.s2/m2") = 0.5*surge.rho*surge.C_d*surge.A "Współczynnik oporu ½·ρ·C_d·A";
  final parameter Modelica.Units.SI.Velocity U_ss = sqrt(T0/k_d) "Prędkość ustalona: T0 = k_d·U²";
  final parameter Modelica.Units.SI.Time tau = (surge.m + surge.m_added_x)/sqrt(T0*k_d) "Stała czasowa rozpędzania";

  FishRobot.Propulsion.SurgeDynamics surge
    annotation (Placement(transformation(extent={{0,-10},{20,10}})));
  Modelica.Blocks.Sources.Constant thrust(k=T0)
    annotation (Placement(transformation(extent={{-60,-10},{-40,10}})));
  Modelica.Units.SI.Velocity U_analytic = U_ss*tanh(time/tau)
    "Rozwiązanie m·U' = T0 - k_d·U² przy U(0) = 0";
equation
  connect(thrust.y, surge.T) annotation (Line(points={{-39,0},{-2,0}}, color={0,0,127}));
  annotation (
    experiment(StopTime=30, Interval=0.01, Tolerance=1e-8),
    Documentation(info="<html>
<p>Stały ciąg 30 mN, ryba startuje z miejsca. Równanie <code>m·U' = T0 - k_d·U<sup>2</sup></code> ma rozwiązanie
<code>U = U_ss·tanh(t/&tau;)</code>, <code>U_ss = &radic;(T0/k_d)</code>, <code>&tau; = m/&radic;(T0·k_d)</code>
(m z masą dodaną). Oczekiwanie: symulacja zgodna z rozwiązaniem (&lt; 0,1% U_ss) – różnicę daje tylko
regularyzacja <code>|U|</code> w pobliżu zera.</p>
</html>"));
end SurgeTerminalVelocity;
