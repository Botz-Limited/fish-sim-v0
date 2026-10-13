within FishRobot.Hydraulics;
model DirectionalValve "Zawór rozdzielający 3/2 (A–P albo A–T) ze skończonym czasem przełączenia"
  import Modelica.Units.SI;

  parameter SI.VolumeFlowRate Q_nom = 4e-5
    "Przepływ przez całkowicie otwartą drogę przy spadku dp_nom (PLACEHOLDER – do identyfikacji)";
  parameter SI.PressureDifference dp_nom = 3e3
    "Spadek ciśnienia odniesienia dla Q_nom (punkt z karty katalogowej, stały)";
  parameter SI.Time tau_valve = 0.02
    "Czas przełączenia: pełny skok suwaka (PLACEHOLDER – do identyfikacji)";
  parameter Real G_leak(unit="m3/(s.Pa)") = 1e-12
    "Przewodność przecieku zamkniętej drogi (PLACEHOLDER – do identyfikacji)";
  parameter SI.PressureDifference dp_small = 50
    "Szerokość regularyzacji kryzy wokół dp = 0 (poniżej przepływ jest liniowy)";
  parameter Real x_eps = 0.01 "Szerokość hamowania suwaka przy końcu skoku (ułamek skoku)";

  FishRobot.Interfaces.HydraulicPort_a port_A "Wyjście robocze (do komory)"
    annotation (Placement(transformation(extent={{-10,90},{10,110}})));
  FishRobot.Interfaces.HydraulicPort_a port_P "Zasilanie (tłoczenie pompy)"
    annotation (Placement(transformation(extent={{-70,-110},{-50,-90}})));
  FishRobot.Interfaces.HydraulicPort_b port_T "Powrót (ssanie pompy)"
    annotation (Placement(transformation(extent={{50,-110},{70,-90}})));
  Modelica.Blocks.Interfaces.BooleanInput energized
    "true: droga P → A otwarta (A–T zamknięta); false: A → T otwarta (A–P zamknięta)"
    annotation (Placement(transformation(extent={{-140,-20},{-100,20}})));

  Real x(min=-0.01, max=1.01) "Położenie suwaka: 0 = A–T, 1 = A–P";
  Real a_PA "Względne otwarcie drogi P → A (0…1)";
  Real a_AT "Względne otwarcie drogi A → T (0…1)";
  SI.PressureDifference dp_PA(nominal=1e4) "Spadek ciśnienia P → A";
  SI.PressureDifference dp_AT(nominal=1e4) "Spadek ciśnienia A → T";
  SI.VolumeFlowRate V_flow_PA(nominal=1e-5) "Przepływ P → A";
  SI.VolumeFlowRate V_flow_AT(nominal=1e-5) "Przepływ A → T";
  SI.Power P_loss "Moc rozpraszana na obu kryzach";

protected
  Real x_set = if energized then 1 else 0 "Położenie docelowe suwaka";
  Real xc = noEvent(max(0, min(1, x))) "Położenie przycięte do [0, 1]";

initial equation
  x = x_set;

equation
  // Suwak jedzie ze stałą prędkością 1/tau_valve i łagodnie hamuje przy końcu skoku (tanh zamiast
  // twardego ogranicznika prędkości – bez zdarzeń, a pełne przełączenie trwa ok. tau_valve).
  der(x) = tanh((x_set - x)/x_eps)/tau_valve;
  // Otwarcia kryz: gładki krok 3x² − 2x³ (zerowa pochodna na końcach skoku). W połowie skoku obie drogi są
  // częściowo otwarte (przejście z przekryciem ujemnym): pompa na chwilę tłoczy prosto do powrotu,
  // ale nigdy nie trafia na zamknięty wylot.
  a_PA = xc^2*(3 - 2*xc);
  a_AT = 1 - a_PA;
  dp_PA = port_P.p - port_A.p;
  dp_AT = port_A.p - port_T.p;
  // Kryza turbulentna Q ~ sqrt(Δp), zregularyzowana wokół zera: dp/sqrt(dp_nom·sqrt(dp² + dp_small²)).
  V_flow_PA = a_PA*Q_nom*dp_PA/sqrt(dp_nom*sqrt(dp_PA^2 + dp_small^2)) + G_leak*dp_PA;
  V_flow_AT = a_AT*Q_nom*dp_AT/sqrt(dp_nom*sqrt(dp_AT^2 + dp_small^2)) + G_leak*dp_AT;
  port_P.V_flow = V_flow_PA;
  port_T.V_flow = -V_flow_AT;
  port_A.V_flow + port_P.V_flow + port_T.V_flow = 0;
  P_loss = dp_PA*V_flow_PA + dp_AT*V_flow_AT;

  annotation (
    Icon(graphics={
      Rectangle(extent={{-90,50},{0,-50}}, lineColor={0,0,0}, fillColor={255,255,255},
        fillPattern=FillPattern.Solid),
      Rectangle(extent={{0,50},{90,-50}}, lineColor={0,0,0}, fillColor={255,255,255},
        fillPattern=FillPattern.Solid),
      Line(points={{-60,-50},{-60,40}}, color={0,128,255}),
      Polygon(points={{-60,45},{-66,30},{-54,30},{-60,45}}, lineColor={0,128,255}, fillColor={0,128,255},
        fillPattern=FillPattern.Solid),
      Line(points={{-30,-50},{-30,-30}}),
      Line(points={{-38,-30},{-22,-30}}),
      Line(points={{30,-50},{30,-30}}),
      Line(points={{22,-30},{38,-30}}),
      Line(points={{60,-50},{60,40}}, color={0,128,255}),
      Polygon(points={{60,-45},{54,-30},{66,-30},{60,-45}}, lineColor={0,128,255}, fillColor={0,128,255},
        fillPattern=FillPattern.Solid),
      Line(points={{0,90},{0,50}}, color={0,128,255}),
      Line(points={{-60,-90},{-60,-50}}, color={0,128,255}),
      Line(points={{60,-90},{60,-50}}, color={0,128,255}),
      Text(extent={{-80,-55},{-40,-85}}, textString="P", textColor={0,0,0}),
      Text(extent={{40,-55},{80,-85}}, textString="T", textColor={0,0,0}),
      Text(extent={{10,90},{50,60}}, textString="A", textColor={0,0,0}),
      Text(extent={{-150,-110},{150,-150}}, textString="%name", textColor={0,0,255})}),
    Documentation(info="<html>
<p>Zawór rozdzielający <b>3/2</b> (trzy drogi, dwa położenia): wyjście robocze <code>A</code> jest połączone albo
z zasilaniem <code>P</code> (cewka załączona, <code>energized = true</code>), albo z powrotem <code>T</code>.
Zawór nie ma położenia „wszystko zamknięte”. Dwa takie zawory (po jednym na komorę) zastępują zawór 4/2:
komora po stronie <code>P</code> się napełnia, a po stronie <code>T</code> opróżnia.</p>
<pre>  dx/dt  = tanh((x_set - x)/x_eps)/tau_valve      x: 0 = A–T, 1 = A–P
  a_PA   = 3x² - 2x³,  a_AT = 1 - a_PA
  Q_PA   = a_PA·Q_nom·sgn(&Delta;p)·sqrt(|&Delta;p|/dp_nom) + G_leak·&Delta;p   (zregularyzowane przy &Delta;p &rarr; 0)</pre>
<p><b>Skończony czas przełączenia:</b> suwak przejeżdża cały skok w czasie ok. <code>tau_valve</code> (stała prędkość,
łagodne hamowanie na końcu). Otwarcie kryzy rośnie gładko z położeniem, więc przepływ w gałęzi odwraca się
w czasie rzędu <code>tau_valve</code>, a nie skokowo.</p>
<p><b>Przekrycie ujemne:</b> w połowie skoku obie drogi są częściowo otwarte i <code>P</code> łączy się z <code>T</code>.
Pompa o stałym wydatku nie trafia wtedy na zamknięty wylot (brak skoku ciśnienia), a część wydatku na chwilę
krąży z pominięciem komór.</p>
<p><b>Kryza:</b> przepływ turbulentny <code>Q ~ sqrt(&Delta;p)</code> opisany punktem z karty katalogowej
(<code>Q_nom</code> przy <code>dp_nom</code>). Z pomiaru da się wyznaczyć tylko iloraz
<code>Q_nom/sqrt(dp_nom)</code>, więc <code>dp_nom</code> zostaje stałe, a dopasowujemy <code>Q_nom</code>
(<code>Calibration.DirectionalValveBench</code>).</p>
<p><b>Energia:</b> <code>P_loss = &Delta;p_PA·Q_PA + &Delta;p_AT·Q_AT &ge; 0</code> – zawór niczego nie magazynuje.</p>
</html>"));
end DirectionalValve;
