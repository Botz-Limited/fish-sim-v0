within FishRobot.Calibration;
model ValveBench "Stanowisko: charakterystyka Q(Δp) zaworu przelewowego (krok 6)"
  extends Modelica.Icons.Example;

  parameter Modelica.Units.SI.PressureDifference dp_lo = 30e3 "Δp na początku rampy (t = 0)";
  parameter Modelica.Units.SI.PressureDifference dp_hi = 60e3 "Δp na końcu rampy (t = 1)";
  parameter Modelica.Units.SI.AbsolutePressure p_ambient = 1.01325e5;

  Modelica.Blocks.Sources.Ramp ramp(offset=p_ambient + dp_lo, height=dp_hi - dp_lo, duration=1, startTime=0)
    "Ciśnienie przed zaworem; chwila t odpowiada Δp = dp_lo + (dp_hi − dp_lo)·t"
    annotation (Placement(transformation(extent={{-90,-10},{-70,10}})));
  FishRobot.Hydraulics.Reservoir inlet(use_p_in=true) "Pompa z kroku 3 (ciśnienie zadane)"
    annotation (Placement(transformation(extent={{-50,-10},{-30,10}})));
  FishRobot.Hydraulics.ReliefValve valve
    annotation (Placement(transformation(extent={{-10,-10},{10,10}})));
  FishRobot.Hydraulics.Reservoir outlet(p=p_ambient)
    annotation (Placement(transformation(extent={{50,-10},{30,10}})));

  Modelica.Units.SI.PressureDifference dp = valve.dp "Różnica ciśnień na zaworze";
  Modelica.Units.SI.VolumeFlowRate Q = valve.V_flow "Przepływ przez zawór";
equation
  connect(ramp.y, inlet.p_in) annotation (Line(points={{-69,0},{-54,0}}, color={0,0,127}));
  connect(inlet.port, valve.port_a) annotation (Line(points={{-30,0},{-10,0}}, color={0,128,255}));
  connect(valve.port_b, outlet.port) annotation (Line(points={{10,0},{30,0}}, color={0,128,255}));
  annotation (
    experiment(StopTime=1.0, Interval=1e-3, Tolerance=1e-8),
    Documentation(info="<html>
<p>Pompa z kroku 3 tłoczy wodę przez zawór przelewowy do zbiornika. Przepływ zwiększa się, a potem
zmniejsza, małymi krokami. W każdym punkcie mierzymy przepływ (przepływomierz) i różnicę ciśnień na zaworze.
Zawór nie ma w modelu dynamiki, więc rampa ciśnienia w czasie służy tylko do przejścia po charakterystyce.</p>
<p>W modelu przewodność otwartego zaworu to <code>G_open = V_flow_nominal/dp_open</code>. Z pomiaru da się
wyznaczyć tylko ten iloraz, więc <code>dp_open</code> zostaje stałe (to tylko punkt odniesienia),
a dopasowujemy <code>V_flow_nominal</code>.</p>
</html>"));
end ValveBench;
