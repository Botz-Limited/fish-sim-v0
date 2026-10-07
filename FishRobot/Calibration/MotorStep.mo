within FishRobot.Calibration;
model MotorStep "Stanowisko: skok napięcia z zasilacza na silnik z wolnym wałem (krok 2 planu kalibracji)"
  extends Modelica.Icons.Example;

  parameter Modelica.Units.SI.Voltage U = 6.0 "Napięcie zasilacza po skoku";
  parameter Modelica.Units.SI.Time t_step = 0.01 "Chwila załączenia zasilacza";

  Modelica.Electrical.Analog.Sources.StepVoltage supply(V=U, startTime=t_step) "Zasilacz laboratoryjny"
    annotation (Placement(transformation(extent={{-10,-10},{10,10}}, rotation=-90, origin={-40,0})));
  FishRobot.Electrical.DCMotor motor
    annotation (Placement(transformation(extent={{0,-10},{20,10}})));
  Modelica.Electrical.Analog.Basic.Ground ground
    annotation (Placement(transformation(extent={{-50,-50},{-30,-30}})));

  // Wielkości mierzone na stole: prąd (bocznik lub sonda prądowa) i prędkość (enkoder lub tachometr)
  Modelica.Units.SI.Current i = motor.i "Prąd silnika";
  Modelica.Units.SI.AngularVelocity w = motor.w "Prędkość wału";
equation
  connect(supply.p, motor.p) annotation (Line(points={{-40,10},{-40,20},{-10,20},{-10,4},{0,4}}, color={0,0,255}));
  connect(supply.n, motor.n) annotation (Line(points={{-40,-10},{-40,-20},{-10,-20},{-10,-4},{0,-4}}, color={0,0,255}));
  connect(ground.p, supply.n) annotation (Line(points={{-40,-30},{-40,-10}}, color={0,0,255}));
  annotation (
    experiment(StopTime=0.3, Interval=1e-4, Tolerance=1e-8),
    Documentation(info="<html>
<p>Silnik z wolnym wałem dostaje skok napięcia z zasilacza laboratoryjnego. Mierzymy prąd <code>i(t)</code>
i prędkość <code>w(t)</code>. Jeden taki rozruch wystarcza do wyznaczenia wszystkich pięciu parametrów
<code>DCMotor</code>, bo każdy z nich kształtuje inną część przebiegu:</p>
<ul>
<li><code>R</code>: szczyt prądu tuż po skoku (wirnik jeszcze stoi, więc <code>i &asymp; U/R</code>),</li>
<li><code>L</code>: czas narastania prądu do szczytu (stała czasowa <code>L/R</code>),</li>
<li><code>k</code>: prędkość ustalona <code>w &asymp; U/k</code>,</li>
<li><code>b</code>: prąd ustalony, który pokrywa tylko tarcie (<code>k·i = b·w</code>),</li>
<li><code>J</code>: czas rozpędzania (stała czasowa mechaniczna <code>J·R/k<sup>2</sup></code>).</li>
</ul>
<p>Rezystancja przewodów i zasilacza wchodzi w wyznaczone <code>R</code>. Jeśli ma być osobno,
trzeba ją zmierzyć i odjąć.</p>
</html>"));
end MotorStep;
