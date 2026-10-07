within FishRobot.Calibration;
model ThrustBench "Stanowisko: średni ciąg płetwy przy zadanym ruchu ogona i prędkości przepływu (krok 9)"
  extends Modelica.Icons.Example;
  import Modelica.Constants.pi;

  parameter Modelica.Units.SI.Angle Theta = 0.3 "Amplituda kąta ogona (zmierzona)";
  parameter Modelica.Units.SI.Frequency f = 1.0 "Częstotliwość machania";
  parameter Modelica.Units.SI.Velocity U0 = 0 "Prędkość przepływu w tunelu (0 = ryba na uwięzi w basenie)";
  final parameter Modelica.Units.SI.AngularFrequency omega = 2*pi*f;

  FishRobot.Propulsion.LighthillFin fin
    annotation (Placement(transformation(extent={{10,-10},{30,10}})));
  Modelica.Mechanics.Rotational.Sources.Move move "Ruch ogona: sinus o zmierzonej amplitudzie"
    annotation (Placement(transformation(extent={{-30,-10},{-10,10}})));

  Modelica.Units.SI.Impulse I_T(start=0, fixed=true) "Całka z ciągu";
  Modelica.Units.SI.Force T_mean = if time > 0 then I_T/time else 0
    "Średni ciąg (dokładny po całkowitej liczbie okresów)";
equation
  move.u = {Theta*sin(omega*time), Theta*omega*cos(omega*time), -Theta*omega^2*sin(omega*time)};
  fin.U = U0;
  der(I_T) = fin.T;
  connect(move.flange, fin.flange) annotation (Line(points={{-10,0},{10,0}}));
  annotation (
    experiment(StopTime=4, Interval=1e-3, Tolerance=1e-8),
    Documentation(info="<html>
<p>Ryba przymocowana do siłomierza, w basenie (<code>U0 = 0</code>) albo w tunelu wodnym. Mierzymy średni ciąg
i amplitudę kąta ogona przy kilku częstotliwościach i prędkościach przepływu. W tunelu siłomierz widzi ciąg
minus opór kadłuba, więc przy każdej prędkości trzeba też zmierzyć siłę przy nieruchomym ogonie (tara)
i ją odjąć.</p>
<p>Model mierzy średni ciąg dla zadanego sinusa kąta. Ciąg jest liniowy w <code>C_T</code>, a
<code>s_fin</code> występuje tylko w iloczynie <code>C_T·s_fin<sup>2</sup></code>, więc <code>s_fin</code> i
<code>L_tail</code> mierzy się linijką, a z pomiaru wyznacza się tylko <code>C_T</code>.</p>
</html>"));
end ThrustBench;
