within FishRobot.Examples;
model TailFlapping "Scenariusz 2: zadana objętość sinusoidalna, regulator przekaźnikowy + zawory 3/2, ogon swobodny"
  extends Modelica.Icons.Example;
  FishRobot.Control.CPG cpg(A_V=4e-6, f=1.5)
    annotation (Placement(transformation(extent={{-60,-10},{-40,10}})));
  FishRobot.Subsystems.TailDrive drive
    annotation (Placement(transformation(extent={{-10,-10},{10,10}})));
equation
  connect(cpg.y, drive.u) annotation (Line(points={{-39,0},{-12,0}}, color={0,0,127}));
  connect(drive.V_p, cpg.V_p) annotation (Line(points={{11,-10},{20,-10},{20,-20},{-70,-20},{-70,0},{-62,0}}, color={0,0,127}));
  annotation (
    experiment(StopTime=5.0, Interval=0.001, Tolerance=1e-6),
    Documentation(info="<html>
<p><b>Scenariusz 2.</b> Zadana objętość przetłoczona: sinus 1,5 Hz (<code>tail_freq_min</code>) o amplitudzie 4 ml.
Pompa kręci się ze stałą prędkością, a regulator przekaźnikowy przełącza zawory 3/2 w stronę <code>V_ref</code>,
przy czym każdy stan zaworu trwa co najmniej <code>valve_min_dwell = 0,2 s</code>. Przy 1,5 Hz
<code>2&pi;f·A_V &asymp; 38 ml/s &gt; Q_const &asymp; 35 ml/s</code>, więc regulator już nie śledzi sinusa: objętość ma
kształt trójkąta o amplitudzie ok. <code>Q_const/(4f) &asymp; 5,9 ml</code> (w symulacji ok. 5 ml), a zawory przełączają się
ok. 2–3 razy na cykl (dodatkowe przełączenie przy szczycie, gdy pompa na chwilę dogoni <code>V_ref</code>).
Obserwuj: prąd silnika jest prawie stały (tylko rozruch w <code>t = 0</code>), a odstęp między przełączeniami nigdy nie
jest krótszy niż 0,2 s.</p>
</html>"));
end TailFlapping;
