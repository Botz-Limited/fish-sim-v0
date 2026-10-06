within FishRobot.Examples;
model SwimForward "Scenariusz 7: machanie ogonem -> ciąg płetwy -> pływanie do przodu"
  extends Modelica.Icons.Example;
  FishRobot.Control.CPG cpg(A=0.8, f=1.0)
    annotation (Placement(transformation(extent={{-80,-10},{-60,10}})));
  FishRobot.Subsystems.TailDrive drive
    annotation (Placement(transformation(extent={{-40,-10},{-20,10}})));
  FishRobot.Propulsion.LighthillFin fin(L_tail=drive.tail.L_tail)
    annotation (Placement(transformation(extent={{0,-50},{20,-30}})));
  FishRobot.Propulsion.SurgeDynamics surge
    annotation (Placement(transformation(extent={{50,-50},{70,-30}})));

  // --- Bilans energii całego robota: bateria -> napęd ogona -> płetwa -> ślad + opór kadłuba
  Modelica.Units.SI.Energy E_thrust(start=0, fixed=true) "Praca ciągu ∫T·U dt";
  Modelica.Units.SI.Energy E_wake(start=0, fixed=true) "Energia zostawiona w śladzie wirowym";
  Modelica.Units.SI.Energy E_drag(start=0, fixed=true) "Praca przeciw oporowi kadłuba (użyteczna)";
  Modelica.Units.SI.Energy E_system_error = drive.E_battery - drive.E_loss_total - E_wake - E_drag
    - surge.E_kin - (drive.E_stored - drive.E_stored0)
    "Błąd bilansu całego robota (ryba startuje z miejsca, więc E_kin(0) = 0)";
  Modelica.Units.SI.Energy E_fin_error = drive.E_mech_out - E_thrust - E_wake
    "Bilans płetwy: energia z ogona = praca ciągu + ślad";
equation
  der(E_thrust) = fin.P_thrust;
  der(E_wake) = fin.P_wake;
  der(E_drag) = surge.P_drag;
  connect(cpg.y, drive.u) annotation (Line(points={{-59,0},{-42,0}}, color={0,0,127}));
  connect(drive.flange_tail, fin.flange) annotation (Line(points={{-30,-10},{-30,-40},{0,-40}}));
  connect(fin.T, surge.T) annotation (Line(points={{21,-40},{48,-40}}, color={0,0,127}));
  connect(surge.U, fin.U) annotation (Line(points={{71,-36},{80,-36},{80,-70},{10,-70},{10,-52}}, color={0,0,127}));
  annotation (
    experiment(StopTime=120, Interval=0.01, Tolerance=1e-6),
    Documentation(info="<html>
<p><b>Scenariusz 7.</b> CPG 1 Hz, amplituda komendy 0,8. Ogon napędzany pompą obraca płetwę
(<code>LighthillFin</code>), płetwa daje ciąg, a ciąg rozpędza rybę (<code>SurgeDynamics</code>).
Płetwa hamuje ogon momentem przez złącze mechaniczne, więc im szybciej ryba płynie, tym więcej mocy
pobiera z napędu.</p>
<p><b>Zastrzeżenie:</b> model ciągu to placeholder (patrz dokumentacja <code>LighthillFin</code>). Prędkości
z tego scenariusza pokazują <i>trendy</i> i rząd wielkości, a nie liczby do projektowania.</p>
<p>Obserwuj: ciąg pulsuje z podwójną częstotliwością (płetwa pcha w obu kierunkach machnięcia), a prędkość ustala się
po kilku sekundach, gdy średni ciąg zrówna się z oporem kadłuba. Bilans energii obejmuje cały robot:
<code>E_system_error</code> = energia z baterii minus straty napędu, ślad wirowy, praca przeciw oporowi
i energia kinetyczna ryby.</p>
<p>Przegląd częstotliwości (prędkość ustalona vs f): <code>scripts/sweep.py --swim</code>.</p>
</html>"));
end SwimForward;
