within FishRobot.Tests;
model FinPrescribedMotion "Test: płetwa z wymuszonym sinusem kąta przy stałej prędkości – średni ciąg i bilans mocy"
  extends Modelica.Icons.Example;
  import Modelica.Constants.pi;
  parameter Modelica.Units.SI.Angle Theta = 0.3 "Amplituda kąta ogona";
  parameter Modelica.Units.SI.Frequency f = 1.0 "Częstotliwość machania";
  parameter Modelica.Units.SI.Velocity U0 = 0.15 "Stała prędkość pływania";
  final parameter Modelica.Units.SI.AngularFrequency omega = 2*pi*f;
  final parameter Modelica.Units.SI.Force T_mean_analytic = 0.25*fin.m_a*Theta^2*((fin.L_tail*omega)^2 - U0^2)
    "Średni ciąg: ¼·m_a·Θ²·(L²ω² - U²)";
  final parameter Real eta_analytic = 0.5*(1 - (U0/(fin.L_tail*omega))^2) "Sprawność: ½·(1 - (U/Lω)²)";

  FishRobot.Propulsion.LighthillFin fin
    annotation (Placement(transformation(extent={{20,-10},{40,10}})));
  Modelica.Mechanics.Rotational.Sources.Move move "Wymuszony kąt, prędkość i przyspieszenie ogona"
    annotation (Placement(transformation(extent={{-20,-10},{0,10}})));

  Modelica.Units.SI.Impulse I_T(start=0, fixed=true) "Całka z ciągu";
  Modelica.Units.SI.Energy E_fin(start=0, fixed=true) "Energia pobrana z ogona";
  Modelica.Units.SI.Energy E_thrust(start=0, fixed=true) "Praca ciągu T·U";
  Modelica.Units.SI.Energy E_wake(start=0, fixed=true) "Energia w śladzie";
  Modelica.Units.SI.Energy E_balance_error = E_fin - E_thrust - E_wake "Powinno być 0";
equation
  move.u = {Theta*sin(omega*time), Theta*omega*cos(omega*time), -Theta*omega^2*sin(omega*time)};
  fin.U = U0;
  der(I_T) = fin.T;
  der(E_fin) = fin.P_fin;
  der(E_thrust) = fin.P_thrust;
  der(E_wake) = fin.P_wake;
  connect(move.flange, fin.flange) annotation (Line(points={{0,0},{20,0}}));
  annotation (
    experiment(StopTime=2, Interval=0.001, Tolerance=1e-8),
    Documentation(info="<html>
<p>Kąt ogona wymuszony sinusem &Theta; = 0,3 rad przy 1 Hz, prędkość stała 15 cm/s (bez dynamiki ruchu).
Po całkowitej liczbie okresów sprawdzamy:</p>
<ul>
<li>średni ciąg <code>I_T/t</code> = <code>&frac14;·m_a·&Theta;<sup>2</sup>·(L<sup>2</sup>&omega;<sup>2</sup> - U<sup>2</sup>)</code> (&lt; 1%),</li>
<li>sprawność <code>E_thrust/E_fin</code> = <code>&frac12;·(1 - (U/L&omega;)<sup>2</sup>)</code> (&lt; 1%),</li>
<li>bilans mocy <code>P_fin = T·U + P_wake</code> (błąd na poziomie numerycznym).</li>
</ul>
</html>"));
end FinPrescribedMotion;
