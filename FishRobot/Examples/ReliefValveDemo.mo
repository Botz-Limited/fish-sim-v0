within FishRobot.Examples;
model ReliefValveDemo "Scenariusz 4: za duże przesunięcie zadanej objętości (skręt) – zawór przelewowy otwiera się i traci energię"
  extends Modelica.Icons.Example;
  FishRobot.Control.CPG cpg(A_V=4e-6, f=1.5, bias_V=14e-6)
    annotation (Placement(transformation(extent={{-60,-10},{-40,10}})));
  FishRobot.Subsystems.TailDrive drive
    annotation (Placement(transformation(extent={{-10,-10},{10,10}})));
  Modelica.Units.SI.Power P_relief = drive.reliefPS.P_loss + drive.reliefSP.P_loss "Moc tracona w zaworach";
  Modelica.Units.SI.Energy E_relief(start=0, fixed=true) "Energia stracona w zaworach";
  Modelica.Units.SI.Energy E_pump_hyd(start=0, fixed=true) "Energia hydrauliczna oddana przez pompę";
equation
  der(E_relief) = P_relief;
  der(E_pump_hyd) = drive.pump.P_hyd;
  connect(cpg.y, drive.u) annotation (Line(points={{-39,0},{-12,0}}, color={0,0,127}));
  connect(drive.V_p, cpg.V_p) annotation (Line(points={{11,-10},{20,-10},{20,-20},{-70,-20},{-70,0},{-62,0}}, color={0,0,127}));
  annotation (
    experiment(StopTime=10.0, Interval=0.002, Tolerance=1e-6),
    Documentation(info="<html>
<p><b>Scenariusz 4.</b> Machanie 1,5 Hz z amplitudą 4 ml wokół przesunięcia <code>bias_V = 14 ml</code> (mocny skręt).
Średnie położenie ogona jest tak daleko, że w każdym cyklu komora L dochodzi do ciśnienia otwarcia zaworu
przelewowego: kąt ogona przestaje rosnąć („spłaszczone” szczyty), a pompa o stałym wydatku dalej tłoczy
i jej moc idzie w ciepło w zaworze.</p>
<p>Dlaczego przesunięcie, a nie sama amplituda: w dozwolonym zakresie częstotliwości
(<code>[tail_freq_min, tail_freq_max] = [1,5; 2,5] Hz</code>, minimalny czas stanu zaworu 0,2 s) zawór przełącza się
około 2 razy na cykl, więc skok objętości jest ograniczony do ok. <code>Q_const/(2f)</code> niezależnie od
<code>A_V</code> (np. <code>A_V = 20 ml</code> daje ten sam ruch co 4 ml). Zawór przelewowy może się więc otworzyć tylko przy
dużym <code>bias_V</code> albo na starcie.</p>
<p>Wniosek projektowy: przy napędzie o stałym wydatku zadane położenie ogona musi mieścić się w tym, co komory
przyjmą poniżej <code>p_set</code>. Inaczej bateria grzeje zawór – i to przy pełnym wydatku, bo pompy nie da się przydławić.</p>
</html>"));
end ReliefValveDemo;
