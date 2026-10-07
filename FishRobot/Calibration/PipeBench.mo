within FishRobot.Calibration;
model PipeBench "Stanowisko: charakterystyka dp(Q) przewodu, przepływ narastający quasi-statycznie (krok 4)"
  extends Modelica.Icons.Example;

  parameter Modelica.Units.SI.VolumeFlowRate Q_max = 4e-5
    "Przepływ na końcu rampy; czas t odpowiada przepływowi Q = Q_max·t (t = 0…1)";
  parameter Modelica.Units.SI.Length l = 0.2 "Długość przewodu (zmierzona linijką, nie dopasowywana)";

  Modelica.Blocks.Sources.Ramp ramp(height=Q_max, duration=1, startTime=0)
    annotation (Placement(transformation(extent={{-80,-10},{-60,10}})));
  FishRobot.Hydraulics.VolumeFlowSource source "Pompa z kroku 3 i przepływomierz"
    annotation (Placement(transformation(extent={{-40,-10},{-20,10}})));
  FishRobot.Hydraulics.Pipe pipe(l=l) "Badany przewód (z kolankami i złączkami jak w robocie)"
    annotation (Placement(transformation(extent={{0,-10},{20,10}})));
  FishRobot.Hydraulics.Reservoir tank
    annotation (Placement(transformation(extent={{60,-10},{40,10}})));

  // Wielkości mierzone: przepływ i spadek ciśnienia (czujnik różnicowy na końcach przewodu)
  Modelica.Units.SI.VolumeFlowRate Q = pipe.V_flow "Przepływ";
  Modelica.Units.SI.PressureDifference dp = pipe.dp "Spadek ciśnienia na przewodzie";
  Real Re = pipe.Re "Liczba Reynoldsa";
equation
  connect(ramp.y, source.V_flow) annotation (Line(points={{-59,0},{-42,0}}, color={0,0,127}));
  connect(source.port, pipe.port_a) annotation (Line(points={{-20,0},{0,0}}, color={0,128,255}));
  connect(pipe.port_b, tank.port) annotation (Line(points={{20,0},{40,0}}, color={0,128,255}));
  annotation (
    experiment(StopTime=1.0, Interval=1e-3, Tolerance=1e-8),
    Documentation(info="<html>
<p>Pompa przetłacza wodę przez badany przewód do zbiornika. W kilkunastu punktach pracy (po ustaleniu
przepływu) mierzymy przepływ <code>Q</code> i spadek ciśnienia <code>&Delta;p</code> czujnikiem różnicowym
na końcach przewodu. Przewód nie ma inertancji, więc charakterystyka jest statyczna, a rampa w czasie
służy tylko do przejścia po przepływach: chwila <code>t</code> odpowiada <code>Q = Q_max·t</code>.</p>
<p>Długość <code>l</code> mierzy się linijką. Dopasowujemy średnicę hydrauliczną <code>d</code>
(rzeczywista średnica wewnętrzna węża bywa mniejsza od nominalnej, a w oporze laminarnym występuje
w czwartej potędze), straty miejscowe <code>zeta</code> i chropowatość <code>roughness</code>.</p>
</html>"));
end PipeBench;
