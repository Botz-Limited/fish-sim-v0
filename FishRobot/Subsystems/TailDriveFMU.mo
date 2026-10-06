within FishRobot.Subsystems;
model TailDriveFMU "Napęd ogona z samymi wejściami/wyjściami sygnałowymi – do eksportu jako FMU"
  Modelica.Blocks.Interfaces.RealInput u "Komenda pompy u ∈ [-1, 1]"
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

  TailDrive drive "Oś ogona (flange_tail) zostaje niepodłączona – ogon bez obciążenia zewnętrznego"
    annotation (Placement(transformation(extent={{-10,-10},{10,10}})));
equation
  connect(u, drive.u) annotation (Line(points={{-120,0},{-12,0}}, color={0,0,127}));
  connect(drive.theta, theta) annotation (Line(points={{11,8},{60,8},{60,80},{110,80}}, color={0,0,127}));
  connect(drive.w_tail, w_tail) annotation (Line(points={{11,5},{64,5},{64,50},{110,50}}, color={0,0,127}));
  connect(drive.tau_tail, tau_tail) annotation (Line(points={{11,2},{68,2},{68,20},{110,20}}, color={0,0,127}));
  connect(drive.p_L, p_L) annotation (Line(points={{11,-1},{72,-1},{72,-10},{110,-10}}, color={0,0,127}));
  connect(drive.p_R, p_R) annotation (Line(points={{11,-4},{68,-4},{68,-40},{110,-40}}, color={0,0,127}));
  connect(drive.i_motor, i_motor) annotation (Line(points={{11,-7},{64,-7},{64,-70},{110,-70}}, color={0,0,127}));
  annotation (
    Icon(graphics={
      Rectangle(extent={{-100,100},{100,-100}}, lineColor={0,0,0}, fillColor={240,248,255},
        fillPattern=FillPattern.Solid),
      Text(extent={{-90,30},{90,-30}}, textString="FMU", textColor={0,0,0}),
      Text(extent={{-150,150},{150,110}}, textString="%name", textColor={0,0,255})}),
    Documentation(info="<html>
<p>Opakowanie <code>TailDrive</code> do eksportu FMU (<code>scripts/export_fmu.py</code>). FMU widzi tylko
sygnały: wejście <code>u</code> i wyjścia kąta, prędkości, momentu, ciśnień i prądu. Złącze mechaniczne
<code>flange_tail</code> z <code>TailDrive</code> zostaje w środku niepodłączone, bo złącza akauzalnego
(kąt + moment jako zmienna przepływowa) nie da się wystawić jako zwykłego wejścia/wyjścia FMU.</p>
<p>Gdyby FMU miał być sprzężony z symulatorem ruchu (np. MuJoCo), trzeba by tu dodać wejście momentu
obciążenia ogona (<code>Modelica.Mechanics.Rotational.Sources.Torque</code> na <code>flange_tail</code>) –
patrz README.</p>
</html>"));
end TailDriveFMU;
