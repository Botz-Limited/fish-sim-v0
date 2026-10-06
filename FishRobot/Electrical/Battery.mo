within FishRobot.Electrical;
model Battery "Bateria: idealne źródło napięcia z rezystancją wewnętrzną"
  parameter Modelica.Units.SI.Voltage U_nom = 7.4 "Napięcie jałowe (np. 2S LiPo) (PLACEHOLDER – do identyfikacji)";
  parameter Modelica.Units.SI.Resistance R_int = 0.05 "Rezystancja wewnętrzna (PLACEHOLDER – do identyfikacji)";

  Modelica.Electrical.Analog.Interfaces.PositivePin p "Biegun dodatni"
    annotation (Placement(transformation(extent={{90,-10},{110,10}})));
  Modelica.Electrical.Analog.Interfaces.NegativePin n "Biegun ujemny"
    annotation (Placement(transformation(extent={{-110,-10},{-90,10}})));

  Modelica.Units.SI.Current i "Prąd oddawany przez baterię";
  Modelica.Units.SI.Voltage v "Napięcie na zaciskach";
  Modelica.Units.SI.Power P_chem "Moc pobierana z ogniwa (U_nom·i)";
  Modelica.Units.SI.Power P_loss "Straty w rezystancji wewnętrznej";
  Modelica.Units.SI.Energy E_drawn(start=0, fixed=true) "Energia pobrana z ogniwa";

protected
  Modelica.Electrical.Analog.Sources.ConstantVoltage cell(V=U_nom) "Idealne ogniwo"
    annotation (Placement(transformation(extent={{-60,-10},{-40,10}})));
  Modelica.Electrical.Analog.Basic.Resistor rInt(R=R_int) "Rezystancja wewnętrzna"
    annotation (Placement(transformation(extent={{20,-10},{40,10}})));
equation
  connect(n, cell.n) annotation (Line(points={{-100,0},{-60,0}}, color={0,0,255}));
  connect(cell.p, rInt.p) annotation (Line(points={{-40,0},{20,0}}, color={0,0,255}));
  connect(rInt.n, p) annotation (Line(points={{40,0},{100,0}}, color={0,0,255}));
  i = -p.i;
  v = p.v - n.v;
  P_chem = U_nom*i;
  P_loss = rInt.LossPower;
  der(E_drawn) = P_chem;
  annotation (
    Icon(graphics={
      Rectangle(extent={{-80,50},{80,-50}}, lineColor={0,0,0}, fillColor={240,240,240},
        fillPattern=FillPattern.Solid),
      Line(points={{-10,30},{-10,-30}}, color={0,0,255}, thickness=0.5),
      Line(points={{10,15},{10,-15}}, color={0,0,255}, thickness=1),
      Line(points={{-90,0},{-10,0}}, color={0,0,255}),
      Line(points={{10,0},{90,0}}, color={0,0,255}),
      Text(extent={{50,40},{80,10}}, textString="+", textColor={0,0,255}),
      Text(extent={{-150,100},{150,60}}, textString="%name", textColor={0,0,255})}),
    Documentation(info="<html>
<p>Najprostszy model baterii: idealne ogniwo <code>U_nom</code> w szeregu z rezystancją <code>R_int</code>.
Napięcie na zaciskach spada pod obciążeniem: <code>v = U_nom - R_int·i</code>.</p>
<p><code>E_drawn = &int; U_nom·i dt</code> to energia pobrana z ogniwa – punkt startowy bilansu energii.
Część tej energii (<code>R_int·i<sup>2</sup></code>) od razu zamienia się w ciepło w samej baterii.</p>
<p>Pominięto: spadek napięcia ze stanem naładowania, dynamikę polaryzacji (obwody RC), temperaturę.
Do oszacowania czasu pracy wystarczy porównać <code>E_drawn</code> z pojemnością w Wh.</p>
</html>"));
end Battery;
