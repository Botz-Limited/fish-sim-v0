within FishRobot.Examples;
model HydraulicsStep "Scenariusz 1: rampa komendy pompy, ogon zablokowany – ciśnienia, przepływ, prąd silnika"
  extends Modelica.Icons.Example;

  parameter Modelica.Units.SI.AbsolutePressure p_ambient = 1.01325e5 "Ciśnienie otoczenia";
  parameter Modelica.Units.SI.Volume V_prefill = 8e-6
    "Wstępne napełnienie obu komór (PLACEHOLDER – do identyfikacji)";

  // --- Elektryka
  FishRobot.Electrical.Battery battery
    annotation (Placement(transformation(extent={{-130,-10},{-110,10}})));
  FishRobot.Electrical.HBridge bridge
    annotation (Placement(transformation(extent={{-100,-10},{-80,10}})));
  FishRobot.Electrical.DCMotor motor
    annotation (Placement(transformation(extent={{-60,-10},{-40,10}})));
  Modelica.Electrical.Analog.Basic.Ground ground
    annotation (Placement(transformation(extent={{-100,-60},{-80,-40}})));
  Modelica.Blocks.Sources.CombiTimeTable command(
    table=[0, 0; 0.1, 0; 0.2, 0.5; 2.0, 0.5; 2.1, 0; 3.0, 0])
    "Komenda u: rampa do 0,5, utrzymanie, rampa do zera"
    annotation (Placement(transformation(extent={{-130,30},{-110,50}})));

  // --- Hydraulika (układ zamknięty: pompa przepompowuje wodę między komorami R i L)
  FishRobot.Hydraulics.GearPump pump "u > 0: przepływ z komory R do L"
    annotation (Placement(transformation(extent={{-10,10},{10,-10}}, rotation=90, origin={-20,0})));
  FishRobot.Hydraulics.Pipe pipeL "Przewód pompa -> komora L"
    annotation (Placement(transformation(extent={{20,30},{40,50}})));
  FishRobot.Hydraulics.Pipe pipeR "Przewód pompa -> komora R"
    annotation (Placement(transformation(extent={{20,-50},{40,-30}})));
  FishRobot.Hydraulics.Chamber chamberL(p_ambient=p_ambient, V_prefill=V_prefill) "Komora lewa"
    annotation (Placement(transformation(extent={{60,50},{80,70}})));
  FishRobot.Hydraulics.Chamber chamberR(p_ambient=p_ambient, V_prefill=V_prefill) "Komora prawa"
    annotation (Placement(transformation(extent={{60,-30},{80,-10}})));
  FishRobot.Hydraulics.ReliefValve reliefLR "Zrzut L -> R przy nadciśnieniu po stronie L"
    annotation (Placement(transformation(extent={{-10,-10},{10,10}}, rotation=-90, origin={0,0})));
  FishRobot.Hydraulics.ReliefValve reliefRL "Zrzut R -> L przy nadciśnieniu po stronie R"
    annotation (Placement(transformation(extent={{-10,-10},{10,10}}, rotation=90, origin={10,0})));

  // --- Wielkości do wykresów
  Modelica.Units.SI.PressureDifference p_L = chamberL.p_gauge "Nadciśnienie w komorze L";
  Modelica.Units.SI.PressureDifference p_R = chamberR.p_gauge "Nadciśnienie w komorze R";
  Modelica.Units.SI.VolumeFlowRate Q_pump = pump.V_flow "Przepływ przez pompę (R -> L)";
  Modelica.Units.SI.VolumeFlowRate Q_relief = reliefLR.V_flow - reliefRL.V_flow "Przepływ przez zawory (L -> R)";
  Modelica.Units.SI.Current i_motor = motor.i "Prąd silnika";
  Modelica.Units.SI.Current i_battery = battery.i "Prąd baterii";

equation
  connect(command.y[1], bridge.u) annotation (Line(points={{-109,40},{-90,40},{-90,12}}, color={0,0,127}));
  connect(battery.p, bridge.bat) annotation (Line(points={{-110,0},{-106,0},{-106,4},{-100,4}}, color={0,0,255}));
  connect(battery.n, bridge.n) annotation (Line(points={{-130,0},{-136,0},{-136,-24},{-90,-24},{-90,-10}}, color={0,0,255}));
  connect(bridge.mot, motor.p) annotation (Line(points={{-80,4},{-60,4}}, color={0,0,255}));
  connect(motor.n, bridge.n) annotation (Line(points={{-60,-4},{-70,-4},{-70,-24},{-90,-24},{-90,-10}}, color={0,0,255}));
  connect(ground.p, bridge.n) annotation (Line(points={{-90,-40},{-90,-10}}, color={0,0,255}));
  connect(motor.flange, pump.flange) annotation (Line(points={{-40,0},{-30,0}}));
  connect(pump.port_b, pipeL.port_a) annotation (Line(points={{-20,10},{-20,40},{20,40}}, color={0,128,255}));
  connect(pipeL.port_b, chamberL.port) annotation (Line(points={{40,40},{70,40},{70,50}}, color={0,128,255}));
  connect(pump.port_a, pipeR.port_a) annotation (Line(points={{-20,-10},{-20,-40},{20,-40}}, color={0,128,255}));
  connect(pipeR.port_b, chamberR.port) annotation (Line(points={{40,-40},{70,-40},{70,-30}}, color={0,128,255}));
  connect(reliefLR.port_a, pump.port_b) annotation (Line(points={{0,10},{0,20},{-20,20},{-20,10}}, color={0,128,255}));
  connect(reliefLR.port_b, pump.port_a) annotation (Line(points={{0,-10},{0,-20},{-20,-20},{-20,-10}}, color={0,128,255}));
  connect(reliefRL.port_a, pump.port_a) annotation (Line(points={{10,-10},{10,-20},{-20,-20},{-20,-10}}, color={0,128,255}));
  connect(reliefRL.port_b, pump.port_b) annotation (Line(points={{10,10},{10,20},{-20,20},{-20,10}}, color={0,128,255}));
  annotation (
    experiment(StopTime=3.0, Interval=0.001, Tolerance=1e-6),
    Diagram(coordinateSystem(extent={{-140,-80},{100,80}})),
    Documentation(info="<html>
<p><b>Scenariusz 1.</b> Bateria &rarr; mostek H &rarr; silnik DC &rarr; pompa zębata &rarr; przewody &rarr; dwie komory.
Ogona jeszcze nie ma, więc komory odkształcają się tylko wbrew własnym ściankom (to odpowiednik
zablokowanego ogona, który niczego nie dokłada do sztywności).</p>
<ol>
<li><b>t = 0,1–0,2 s:</b> komenda rośnie do 0,5. Silnik rozpędza się, pompa przepompowuje wodę z komory R do L.
Prąd rozruchowy jest wysoki (mała prędkość = małe napięcie indukowane).</li>
<li><b>t &asymp; 0,2–1,5 s:</b> komora L pęcznieje, R się opróżnia. Różnica ciśnień rośnie coraz szybciej
(silikon sztywnieje), silnik zwalnia, prąd rośnie – moment potrzebny do pompowania to <code>D·&Delta;p/&eta;</code>.</li>
<li><b>Gdy &Delta;p dojdzie do p_set:</b> otwiera się zawór <code>reliefLR</code> i ciecz krąży w pętli pompa &rarr; zawór.
Komory przestają się zmieniać, a cała moc pompy zamienia się w ciepło w zaworze.</li>
<li><b>t = 2,0–2,1 s:</b> komenda wraca do zera. Mostek zwiera silnik (v = 0), a sprężyste komory
wypychają wodę z powrotem przez pompę, napędzając ją wstecz – pompa pracuje jako silnik hydrauliczny,
a silnik DC jako hamulec prądnicowy (ujemny prąd).</li>
</ol>
<p>Konwencja: <code>u &gt; 0</code> &rArr; <code>&omega; &gt; 0</code> &rArr; przepływ R &rarr; L &rArr; <code>p_L &gt; p_R</code>.</p>
</html>"));
end HydraulicsStep;
