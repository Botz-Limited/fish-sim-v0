within FishRobot.Calibration;
model TailDecay "Stanowisko: drgania swobodne ogona po wychyleniu, komory odpowietrzone (krok 8)"
  extends Modelica.Icons.Example;

  parameter Modelica.Units.SI.Angle theta0 = 0.3 "Wychylenie początkowe (ogon puszczony z bezruchu)";
  parameter Modelica.Units.SI.AbsolutePressure p_ambient = 1.01325e5;

  FishRobot.Tail.TailEquivalent tail(theta_start=theta0)
    annotation (Placement(transformation(extent={{-10,-10},{10,10}})));
  FishRobot.Hydraulics.Reservoir vent(p=p_ambient) "Obie komory otwarte do zbiornika: Δp = 0"
    annotation (Placement(transformation(extent={{-60,-10},{-40,10}})));

  Modelica.Units.SI.Angle theta = tail.theta "Kąt ogona (enkoder na osi albo kamera)";
equation
  connect(vent.port, tail.port_L) annotation (Line(points={{-40,0},{-26,0},{-26,4},{-10,4}}, color={0,128,255}));
  connect(vent.port, tail.port_R) annotation (Line(points={{-40,0},{-26,0},{-26,-4},{-10,-4}}, color={0,128,255}));
  annotation (
    experiment(StopTime=1.5, Interval=1e-3, Tolerance=1e-8),
    Documentation(info="<html>
<p>Ogon wychylony o <code>theta0</code> i puszczony. Komory są otwarte do zbiornika, więc hydraulika
nie dokłada sztywności ani tłumienia i zostaje sam oscylator:</p>
<pre>  (J + J_added)·&theta;'' + c·&theta;' + c_h·|&theta;'|·&theta;' + k·&theta; = 0</pre>
<p>W powietrzu <code>J_added = 0</code> i <code>c_h &asymp; 0</code>, w wodzie dochodzi masa dodana i opór
kwadratowy. Z samego przebiegu &theta;(t) wynikają tylko ilorazy przez bezwładność
(<code>k/J</code>, <code>c/J</code>), więc <code>k</code> musi być znane z pomiaru statycznego (krok 7).</p>
</html>"));
end TailDecay;
