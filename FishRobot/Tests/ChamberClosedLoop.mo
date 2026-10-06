within FishRobot.Tests;
model ChamberClosedLoop "Test: dwie komory połączone rurą – zachowanie objętości i wyrównanie ciśnień"
  extends Modelica.Icons.Example;

  FishRobot.Hydraulics.Chamber chamberL(V_prefill=8e-6) "Komora lewa, przepełniona na starcie"
    annotation (Placement(transformation(extent={{-60,10},{-40,30}})));
  FishRobot.Hydraulics.Chamber chamberR(V_prefill=3e-6) "Komora prawa, niedopełniona na starcie"
    annotation (Placement(transformation(extent={{40,10},{60,30}})));
  FishRobot.Hydraulics.Pipe pipe(useInertance=true)
    annotation (Placement(transformation(extent={{-10,-30},{10,-10}})));

  Modelica.Units.SI.Volume V_total = chamberL.V + chamberR.V "Suma objętości (ma być stała)";
  Modelica.Units.SI.Energy E_stored = chamberL.E_elastic + chamberR.E_elastic
    + pipe.L_inert*pipe.V_flow^2/2 "Energia zmagazynowana (ścianki + słup cieczy)";
  Modelica.Units.SI.Energy E_dissipated(start=0, fixed=true) "Energia rozproszona w rurze";
equation
  der(E_dissipated) = pipe.P_loss;
  connect(chamberL.port, pipe.port_a) annotation (Line(points={{-50,10},{-50,-20},{-10,-20}}, color={0,128,255}));
  connect(pipe.port_b, chamberR.port) annotation (Line(points={{10,-20},{50,-20},{50,10}}, color={0,128,255}));
  annotation (
    experiment(StopTime=8.0, Interval=0.002, Tolerance=1e-8),
    Documentation(info="<html>
<p>Układ zamknięty jak w robocie: dwie komory połączone przewodem z inertancją. Lewa startuje
z 8 ml, prawa z 3 ml. Ciecz przepływa z komory o wyższym ciśnieniu do niższej, przelatuje
„za daleko” (bezwładność słupa) i oscyluje z tłumieniem, aż ciśnienia się wyrównają.</p>
<p>Oczekiwania: <code>V_total</code> stałe (&lt; 1e-9 względnie), na końcu <code>V_L = V_R = 5,5 ml</code>
(krzywe komór są takie same), a spadek energii zmagazynowanej równa się energii rozproszonej w rurze.</p>
<p>To jest obwód LC z rezystancją: podatność komór (C), inertancja słupa (L), opór rury (R).</p>
</html>"));
end ChamberClosedLoop;
