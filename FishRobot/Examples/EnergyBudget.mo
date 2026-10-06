within FishRobot.Examples;
model EnergyBudget "Scenariusz 5: 60 s pływania – rozkład strat energii i szacowany czas pracy na baterii"
  extends Modelica.Icons.Example;
  parameter Real capacity_Wh = 16.3 "Pojemność baterii, np. 2S 2200 mAh (PLACEHOLDER – do identyfikacji)";

  FishRobot.Control.CPG cpg(A=0.8, f=1.0)
    annotation (Placement(transformation(extent={{-60,-10},{-40,10}})));
  FishRobot.Subsystems.TailDrive drive
    annotation (Placement(transformation(extent={{-10,-10},{10,10}})));

  Modelica.Units.SI.Power P_battery_mean = if time > 1 then drive.E_battery/time else 0
    "Średnia moc pobierana z baterii od startu";
  Modelica.Units.SI.Time t_runtime = if P_battery_mean > 1e-6 then capacity_Wh*3600/P_battery_mean else 0
    "Szacowany czas pracy na baterii (tylko napęd ogona)";
equation
  connect(cpg.y, drive.u) annotation (Line(points={{-39,0},{-12,0}}, color={0,0,127}));
  annotation (
    experiment(StopTime=60, Interval=0.01, Tolerance=1e-6),
    Documentation(info="<html>
<p><b>Scenariusz 5.</b> Minuta machania ogonem (1 Hz, amplituda komendy 0,8). Na końcu sprawdzamy,
gdzie podziała się energia pobrana z baterii: każda strata jest całkowana osobno w <code>TailDrive</code>.</p>
<p><b>Test poprawności całego modelu:</b> suma strat + zmiana energii zmagazynowanej musi się równać
energii z ogniwa (błąd &lt; 1%). Jeśli jakiś komponent tworzył albo gubił energię (zły znak, brakujący
człon, niespójne równania), bilans by się nie zamknął.</p>
<p><code>t_runtime</code> to szacowany czas pracy samego napędu ogona przy placeholderowej pojemności baterii.
Nie obejmuje elektroniki, balastu ani sterowania.</p>
</html>"));
end EnergyBudget;
