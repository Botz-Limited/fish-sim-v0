within FishRobot.Calibration;
model DirectionalValveBench "Stanowisko: przełączanie zaworu rozdzielającego 3/2 przy stałym Δp (Q_nom, tau_valve)"
  extends Modelica.Icons.Example;

  parameter Modelica.Units.SI.PressureDifference dp_test = 5e3 "Nadciśnienie zasilania P względem T i A";
  parameter Modelica.Units.SI.Time t_on = 0.02 "Załączenie cewki (A–T -> A–P)";
  parameter Modelica.Units.SI.Time t_off = 0.07 "Wyłączenie cewki (A–P -> A–T)";
  parameter Modelica.Units.SI.AbsolutePressure p_ambient = 1.01325e5;

  Modelica.Blocks.Sources.BooleanTable coil(table={t_on, t_off}, startValue=false) "Sygnał cewki zaworu"
    annotation (Placement(transformation(extent={{-90,-10},{-70,10}})));
  FishRobot.Hydraulics.Reservoir supply(p=p_ambient + dp_test) "Zasilanie P (zbiornik ciśnieniowy)"
    annotation (Placement(transformation(extent={{-60,-50},{-40,-30}})));
  FishRobot.Hydraulics.Reservoir tank(p=p_ambient) "Powrót T"
    annotation (Placement(transformation(extent={{60,-50},{40,-30}})));
  FishRobot.Hydraulics.Reservoir outlet(p=p_ambient) "Wyjście A przez przepływomierz do zbiornika"
    annotation (Placement(transformation(extent={{60,30},{40,50}})));
  FishRobot.Hydraulics.DirectionalValve valve
    annotation (Placement(transformation(extent={{-10,-10},{10,10}})));

  Modelica.Units.SI.VolumeFlowRate Q = -valve.port_A.V_flow "Przepływ z wyjścia A (przepływomierz)";
equation
  connect(coil.y, valve.energized) annotation (Line(points={{-69,0},{-12,0}}, color={255,0,255}));
  connect(supply.port, valve.port_P) annotation (Line(points={{-40,-40},{-6,-40},{-6,-10}}, color={0,128,255}));
  connect(tank.port, valve.port_T) annotation (Line(points={{40,-40},{6,-40},{6,-10}}, color={0,128,255}));
  connect(outlet.port, valve.port_A) annotation (Line(points={{40,40},{0,40},{0,10}}, color={0,128,255}));
  annotation (
    experiment(StopTime=0.1, Interval=2e-4, Tolerance=1e-8),
    Documentation(info="<html>
<p>Zawór 3/2 zasilany ze zbiornika ciśnieniowego (<code>P</code> = <code>dp_test</code> nad otoczeniem), powrót
<code>T</code> i wyjście <code>A</code> do zbiornika otwartego, na wyjściu <code>A</code> szybki przepływomierz.
Cewka załącza się w <code>t_on</code> i wyłącza w <code>t_off</code>.</p>
<ul>
<li><b>Stan ustalony</b> po załączeniu: <code>Q = Q_nom·sqrt(dp_test/dp_nom)</code> &rarr; <code>Q_nom</code>
(<code>dp_nom</code> jest stałym punktem odniesienia z karty katalogowej).</li>
<li><b>Narastanie i opadanie</b> przepływu: kształt wynika z ruchu suwaka &rarr; <code>tau_valve</code>
(czas przełączenia, ten sam, co w <code>Subsystems.TailDrive</code>).</li>
</ul>
<p>Po wyłączeniu <code>A</code> łączy się z <code>T</code>; oba są pod ciśnieniem otoczenia, więc przepływ spada do zera.</p>
</html>"));
end DirectionalValveBench;
