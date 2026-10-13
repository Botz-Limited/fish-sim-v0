within FishRobot.Subsystems;
model TailDrive "Napęd ogona: bateria + silnik + pompa o stałych obrotach + 2 zawory 3/2 + przewody + komory + ogon"
  parameter Modelica.Units.SI.AbsolutePressure p_ambient = 1.01325e5 "Ciśnienie otoczenia";
  parameter Modelica.Units.SI.Volume V_prefill = 8e-6
    "Wstępne napełnienie obu komór (PLACEHOLDER – do identyfikacji)";
  parameter Modelica.Units.SI.PressureDifference p_set = 50e3
    "Ciśnienie otwarcia zaworów przelewowych (PLACEHOLDER – do identyfikacji)";
  parameter Modelica.Units.SI.VolumeFlowRate V_flow_relief = 4e-5
    "Przepływ nominalny zaworów przelewowych; musi przejąć cały wydatek pompy przy zablokowanym ogonie (PLACEHOLDER)";
  parameter Modelica.Units.SI.Time tau_valve = 0.02
    "Czas przełączenia zaworów rozdzielających (PLACEHOLDER – do identyfikacji)";
  parameter Real u_dir = 0.01 "Próg komendy, powyżej którego |u| przełącza zawory (u = 0: kierunek bez zmian)";
  final parameter Modelica.Units.SI.VolumeFlowRate Q_const = pump.D*battery.U_nom/motor.k
    "Wydatek pompy bez obciążenia D·U_nom/k (rzeczywisty jest mniejszy o spadek obrotów i przeciek)";

  // --- Wejście i wyjścia (interfejs FMU)
  Modelica.Blocks.Interfaces.RealInput u
    "Komenda: znak = kierunek zaworów (+1: R → L, -1: L → R), |u| = załączenie silnika (0 = pompa stoi)"
    annotation (Placement(transformation(extent={{-140,-20},{-100,20}})));
  Modelica.Blocks.Interfaces.RealOutput theta(unit="rad") "Kąt ogona"
    annotation (Placement(transformation(extent={{100,70},{120,90}})));
  Modelica.Blocks.Interfaces.RealOutput w_tail(unit="rad/s") "Prędkość kątowa ogona"
    annotation (Placement(transformation(extent={{100,40},{120,60}})));
  Modelica.Blocks.Interfaces.RealOutput tau_tail(unit="N.m") "Moment hydrauliczny na ogonie"
    annotation (Placement(transformation(extent={{100,10},{120,30}})));
  Modelica.Blocks.Interfaces.RealOutput p_L(unit="Pa") "Nadciśnienie w komorze L"
    annotation (Placement(transformation(extent={{100,-20},{120,0}})));
  Modelica.Blocks.Interfaces.RealOutput p_R(unit="Pa") "Nadciśnienie w komorze R"
    annotation (Placement(transformation(extent={{100,-50},{120,-30}})));
  Modelica.Blocks.Interfaces.RealOutput i_motor(unit="A") "Prąd silnika pompy"
    annotation (Placement(transformation(extent={{100,-80},{120,-60}})));
  Modelica.Blocks.Interfaces.RealOutput V_p(unit="m3")
    "Objętość przetłoczona z gałęzi R do L (całka przepływów w przewodach) – sprzężenie zwrotne regulatora"
    annotation (Placement(transformation(extent={{100,-110},{120,-90}})));
  Modelica.Mechanics.Rotational.Interfaces.Flange_b flange_tail
    "Oś ogona na zewnątrz, np. do płetwy (LighthillFin). Niepodłączona = brak obciążenia"
    annotation (Placement(transformation(extent={{-10,-110},{10,-90}})));

  // --- Elektryka
  FishRobot.Electrical.Battery battery
    annotation (Placement(transformation(extent={{-90,-50},{-70,-30}})));
  FishRobot.Electrical.HBridge bridge(reversible=false) "Tylko wyłącznik silnika – bez odwracania napięcia"
    annotation (Placement(transformation(extent={{-60,-50},{-40,-30}})));
  FishRobot.Electrical.DCMotor motor
    annotation (Placement(transformation(extent={{-30,-50},{-10,-30}})));
  Modelica.Electrical.Analog.Basic.Ground ground
    annotation (Placement(transformation(extent={{-60,-90},{-40,-70}})));

  // --- Hydraulika
  FishRobot.Hydraulics.GearPump pump "Stałe obroty: zawsze tłoczy z port_a (ssanie S) do port_b (tłoczenie P)"
    annotation (Placement(transformation(extent={{-10,10},{10,-10}}, rotation=90, origin={10,-40})));
  FishRobot.Hydraulics.DirectionalValve valveL(tau_valve=tau_valve) "3/2 komory L: załączony = L do tłoczenia"
    annotation (Placement(transformation(extent={{14,10},{34,30}})));
  FishRobot.Hydraulics.DirectionalValve valveR(tau_valve=tau_valve) "3/2 komory R: załączony = R do tłoczenia"
    annotation (Placement(transformation(extent={{14,-80},{34,-60}})));
  FishRobot.Hydraulics.Pipe pipeL "Przewód zawór L -> komora L"
    annotation (Placement(transformation(extent={{30,10},{50,30}})));
  FishRobot.Hydraulics.Pipe pipeR "Przewód zawór R -> komora R"
    annotation (Placement(transformation(extent={{30,-80},{50,-60}})));
  FishRobot.Hydraulics.Chamber chamberL(p_ambient=p_ambient, V_prefill=V_prefill) "Komora lewa"
    annotation (Placement(transformation(extent={{50,40},{70,60}})));
  FishRobot.Hydraulics.Chamber chamberR(p_ambient=p_ambient, V_prefill=V_prefill) "Komora prawa"
    annotation (Placement(transformation(extent={{50,-50},{70,-30}})));
  FishRobot.Hydraulics.ReliefValve reliefPS(p_set=p_set, V_flow_nominal=V_flow_relief)
    "Zrzut tłoczenie -> ssanie (przejmuje wydatek pompy, gdy ogon nie może się ruszyć)"
    annotation (Placement(transformation(extent={{-10,-10},{10,10}}, rotation=-90, origin={-10,0})));
  FishRobot.Hydraulics.ReliefValve reliefSP(p_set=p_set, V_flow_nominal=V_flow_relief)
    "Zrzut ssanie -> tłoczenie (gdy obciążenie zewnętrzne ogona tłoczy ciecz wstecz)"
    annotation (Placement(transformation(extent={{-10,-10},{10,10}}, rotation=90, origin={-30,0})));

  // --- Ogon
  FishRobot.Tail.TailEquivalent tail
    annotation (Placement(transformation(extent={{70,-10},{90,10}})));

  // --- Bilans energii: energia z ogniwa = straty + przyrost energii zmagazynowanej
  Modelica.Units.SI.Energy E_battery = battery.E_drawn "Energia pobrana z ogniwa baterii";
  Modelica.Units.SI.Energy E_loss_battery(start=0, fixed=true) "Straty: rezystancja wewnętrzna baterii";
  Modelica.Units.SI.Energy E_loss_motor_cu(start=0, fixed=true) "Straty: uzwojenie silnika R·i²";
  Modelica.Units.SI.Energy E_loss_motor_fric(start=0, fixed=true) "Straty: łożyska silnika";
  Modelica.Units.SI.Energy E_loss_pump_leak(start=0, fixed=true) "Straty: przeciek w pompie";
  Modelica.Units.SI.Energy E_loss_pump_mech(start=0, fixed=true) "Straty: tarcie w pompie (η_m)";
  Modelica.Units.SI.Energy E_loss_pipes(start=0, fixed=true) "Straty: przewody";
  Modelica.Units.SI.Energy E_loss_relief(start=0, fixed=true) "Straty: zawory przelewowe";
  Modelica.Units.SI.Energy E_loss_valves(start=0, fixed=true) "Straty: zawory rozdzielające 3/2";
  Modelica.Units.SI.Energy E_loss_tail(start=0, fixed=true) "Rozproszone w wodzie i materiale ogona";
  Modelica.Units.SI.Energy E_loss_total = E_loss_battery + E_loss_motor_cu + E_loss_motor_fric
    + E_loss_pump_leak + E_loss_pump_mech + E_loss_pipes + E_loss_relief + E_loss_valves + E_loss_tail "Suma strat";
  Modelica.Units.SI.Energy E_mech_out(start=0, fixed=true)
    "Energia oddana przez oś ogona na zewnątrz (flange_tail), np. płetwie";
  Modelica.Units.SI.Energy E_stored = 0.5*motor.J*motor.w^2 + 0.5*motor.L*motor.i^2
    + chamberL.E_elastic + chamberR.E_elastic + tail.E_kin + tail.E_spring
    "Energia zmagazynowana: wirnik, indukcyjność, ścianki komór, ogon (kinetyczna + sprężysta)";
  parameter Modelica.Units.SI.Energy E_stored0(fixed=false) "Energia zmagazynowana na starcie";
  Modelica.Units.SI.Energy E_balance_error = E_battery - E_loss_total - E_mech_out - (E_stored - E_stored0)
    "Błąd bilansu (powinien być ~0)";

  // --- Kierunek zaworów: pamiętany stan, bez położenia „zamknięte”
  Boolean dirRL(start=true, fixed=true) "true: pompa tłoczy R → L (zawór L załączony), false: L → R";
  Integer n_switch(start=0, fixed=true) "Liczba przełączeń zaworów od startu";

initial equation
  E_stored0 = E_stored;
  V_p = 0;

equation
  // Znak komendy wybiera kierunek; przy u = 0 zawory zostają w ostatnim położeniu (pompa wtedy stoi).
  when {initial(), u > u_dir, u < -u_dir} then
    dirRL = if u > u_dir then true elseif u < -u_dir then false else pre(dirRL);
  end when;
  when change(dirRL) then
    n_switch = pre(n_switch) + 1;
  end when;
  valveL.energized = dirRL;
  valveR.energized = not dirRL;
  bridge.u = abs(u);
  der(V_p) = (pipeL.V_flow - pipeR.V_flow)/2;
  der(E_loss_battery) = battery.P_loss;
  der(E_loss_motor_cu) = motor.P_cu;
  der(E_loss_motor_fric) = motor.P_fric;
  der(E_loss_pump_leak) = pump.P_loss_leak;
  der(E_loss_pump_mech) = pump.P_loss_mech;
  der(E_loss_pipes) = pipeL.P_loss + pipeR.P_loss;
  der(E_loss_relief) = reliefPS.P_loss + reliefSP.P_loss;
  der(E_loss_valves) = valveL.P_loss + valveR.P_loss;
  der(E_loss_tail) = tail.P_water;
  // Moc wpływająca do komponentu przez złącze to tau·w, więc moc wypływająca to -tau·w.
  der(E_mech_out) = -flange_tail.tau*tail.w;
  connect(tail.flange, flange_tail) annotation (Line(points={{90,0},{94,0},{94,-90},{0,-90},{0,-100}}));
  connect(battery.p, bridge.bat) annotation (Line(points={{-70,-40},{-66,-40},{-66,-36},{-60,-36}}, color={0,0,255}));
  connect(battery.n, bridge.n) annotation (Line(points={{-90,-40},{-94,-40},{-94,-60},{-50,-60},{-50,-50}}, color={0,0,255}));
  connect(bridge.mot, motor.p) annotation (Line(points={{-40,-36},{-30,-36}}, color={0,0,255}));
  connect(motor.n, bridge.n) annotation (Line(points={{-30,-44},{-34,-44},{-34,-60},{-50,-60},{-50,-50}}, color={0,0,255}));
  connect(ground.p, bridge.n) annotation (Line(points={{-50,-70},{-50,-50}}, color={0,0,255}));
  connect(motor.flange, pump.flange) annotation (Line(points={{-10,-40},{0,-40}}));
  connect(pump.port_b, valveL.port_P) annotation (Line(points={{10,-30},{10,10},{18,10}}, color={0,128,255}));
  connect(pump.port_b, valveR.port_P) annotation (Line(points={{10,-30},{4,-30},{4,-84},{18,-84},{18,-80}}, color={0,128,255}));
  connect(pump.port_a, valveL.port_T) annotation (Line(points={{10,-50},{30,-50},{30,10}}, color={0,128,255}));
  connect(pump.port_a, valveR.port_T) annotation (Line(points={{10,-50},{10,-86},{30,-86},{30,-80}}, color={0,128,255}));
  connect(valveL.port_A, pipeL.port_a) annotation (Line(points={{24,30},{24,34},{28,34},{28,20},{30,20}}, color={0,128,255}));
  connect(valveR.port_A, pipeR.port_a) annotation (Line(points={{24,-60},{24,-56},{28,-56},{28,-70},{30,-70}}, color={0,128,255}));
  connect(pipeL.port_b, chamberL.port) annotation (Line(points={{50,20},{60,20},{60,40}}, color={0,128,255}));
  connect(pipeR.port_b, chamberR.port) annotation (Line(points={{50,-70},{60,-70},{60,-50}}, color={0,128,255}));
  connect(pipeL.port_b, tail.port_L) annotation (Line(points={{50,20},{64,20},{64,4},{70,4}}, color={0,128,255}));
  connect(pipeR.port_b, tail.port_R) annotation (Line(points={{50,-70},{66,-70},{66,-4},{70,-4}}, color={0,128,255}));
  connect(reliefPS.port_a, pump.port_b) annotation (Line(points={{-10,10},{-10,20},{10,20},{10,-30}}, color={0,128,255}));
  connect(reliefPS.port_b, pump.port_a) annotation (Line(points={{-10,-10},{-10,-20},{4,-20},{4,-56},{10,-56},{10,-50}}, color={0,128,255}));
  connect(reliefSP.port_a, pump.port_a) annotation (Line(points={{-30,-10},{-30,-20},{4,-20},{4,-56},{10,-56},{10,-50}}, color={0,128,255}));
  connect(reliefSP.port_b, pump.port_b) annotation (Line(points={{-30,10},{-30,20},{10,20},{10,-30}}, color={0,128,255}));
  theta = tail.theta;
  w_tail = tail.w;
  tau_tail = tail.tau_hyd;
  p_L = chamberL.p_gauge;
  p_R = chamberR.p_gauge;
  i_motor = motor.i;
  annotation (
    Icon(graphics={
      Rectangle(extent={{-100,100},{100,-100}}, lineColor={0,0,0}, fillColor={240,248,255},
        fillPattern=FillPattern.Solid),
      Text(extent={{-90,60},{90,20}}, textString="M → P → 2×3/2", textColor={0,0,0}),
      Polygon(points={{-20,-20},{40,0},{60,20},{55,-20},{60,-60},{40,-40},{-20,-20}}, lineColor={0,0,0},
        fillColor={255,170,85}, fillPattern=FillPattern.Solid),
      Text(extent={{-150,150},{150,110}}, textString="%name", textColor={0,0,255})}),
    Documentation(info="<html>
<p>Cały napęd ogona w jednym bloku z wejściem <code>u</code> i wyjściami sygnałowymi – to jest podukład
eksportowany jako FMU w etapie 8. Wewnątrz: bateria &rarr; mostek H (tylko wyłącznik) &rarr; silnik DC &rarr;
pompa zębata o stałych obrotach &rarr; dwa zawory rozdzielające 3/2 &rarr; przewody &rarr; komory L/R &rarr; ogon 1 DOF.
Zawory przelewowe (przeciwsobne) leżą między tłoczeniem i ssaniem pompy.</p>
<p><b>Napęd o stałym wydatku:</b> silnik dostaje stałe napięcie i kręci pompę zawsze w tę samą stronę,
więc pompa daje w przybliżeniu stały wydatek <code>Q_const &asymp; D·U_nom/k</code> (minus spadek obrotów pod
obciążeniem i przeciek). Kierunek przepływu wybierają zawory: <code>dirRL = true</code> &rArr; zawór L łączy komorę L
z tłoczeniem, a zawór R komorę R ze ssaniem (R &rarr; L); <code>dirRL = false</code> odwrotnie. Zawory nie mają
położenia „zamknięte”, przełączają się w czasie <code>tau_valve</code>.</p>
<p><b>Wejście <code>u</code>:</b> znak wybiera kierunek (<code>u &gt; 0</code>: R &rarr; L, <code>u &lt; 0</code>: L &rarr; R),
<code>|u|</code> idzie na mostek jako załączenie silnika (<code>u = &plusmn;1</code> – pełne napięcie).
<code>u = 0</code> oznacza „pompa wyłączona”; zawory zostają wtedy w ostatnim położeniu.
<code>n_switch</code> liczy przełączenia zaworów, a <code>V_p</code> (całka przepływów w przewodach) jest sprzężeniem
zwrotnym regulatora przekaźnikowego <code>Control.CPG</code>.</p>
<p><b>Zawory przelewowe</b> muszą przejąć <b>cały</b> wydatek pompy, gdy ogon nie może się ruszyć (np. zablokowany,
<code>Tests.TailBlocked</code>), dlatego <code>V_flow_relief &gt; Q_const</code>.</p>
<p>Wszystkie komponenty są publiczne, więc parametry można zmieniać modyfikatorami, np.
<code>TailDrive drive(motor(R=0.8), tail(k=0.4))</code>, a w OMEdit przez okno parametrów.</p>
<p><b>Bilans energii</b> (zmienne <code>E_*</code>): każda strata jest całkowana osobno, a
<code>E_balance_error = E_battery - E_loss_total - E_mech_out - (E_stored - E_stored0)</code> sprawdza, czy model nie tworzy
ani nie gubi energii. Mostek H jest bezstratny, a moc „ciśnienia otoczenia” znosi się w obiegu zamkniętym
(objętość krąży, nie znika), dlatego nie ma ich na liście. <code>E_mech_out</code> to energia oddana przez złącze <code>flange_tail</code>
(np. płetwie, która zamienia ją na ciąg); bez podłączenia jest zerowa. Pompa pracuje bez przerwy, więc
straty silnika i pompy płyną także wtedy, gdy ogon stoi.</p>
<p>Konwencja: <code>u &gt; 0</code> &rArr; zawory R &rarr; L &rArr; <code>p_L &gt; p_R</code> &rArr; <code>&theta; &gt; 0</code>.</p>
</html>"));
end TailDrive;
