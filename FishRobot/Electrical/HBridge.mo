within FishRobot.Electrical;
model HBridge "Idealny mostek H: v_mot = u·v_bat, bez strat (wspólny biegun ujemny)"
  Modelica.Blocks.Interfaces.RealInput u "Komenda wypełnienia PWM, u ∈ [-1, 1]"
    annotation (Placement(transformation(extent={{-20,-20},{20,20}}, rotation=-90, origin={0,120})));
  Modelica.Electrical.Analog.Interfaces.PositivePin bat "Do bieguna + baterii"
    annotation (Placement(transformation(extent={{-110,30},{-90,50}})));
  Modelica.Electrical.Analog.Interfaces.PositivePin mot "Do zacisku + silnika"
    annotation (Placement(transformation(extent={{90,30},{110,50}})));
  Modelica.Electrical.Analog.Interfaces.NegativePin n "Wspólny biegun ujemny (bateria i silnik)"
    annotation (Placement(transformation(extent={{-10,-110},{10,-90}})));

  Real u_lim "Komenda po nasyceniu do [-1, 1]";
  Modelica.Units.SI.Voltage v_bat "Napięcie zasilania";
  Modelica.Units.SI.Voltage v_mot "Napięcie podawane na silnik";
  Modelica.Units.SI.Current i_mot "Prąd płynący do silnika";
  Modelica.Units.SI.Current i_bat "Prąd pobierany z baterii";
equation
  // noEvent: nasycenie jest ciągłe, więc nie potrzebuje zdarzeń (oszczędzamy restarty solvera).
  u_lim = noEvent(max(-1, min(1, u)));
  v_bat = bat.v - n.v;
  v_mot = mot.v - n.v;
  i_mot = -mot.i;
  i_bat = bat.i;
  v_mot = u_lim*v_bat;
  // Brak strat: moc z baterii = moc do silnika  =>  v_bat·i_bat = u·v_bat·i_mot  =>  i_bat = u·i_mot.
  i_bat = u_lim*i_mot;
  bat.i + mot.i + n.i = 0;
  annotation (
    Icon(graphics={
      Rectangle(extent={{-90,90},{90,-90}}, lineColor={0,0,0}, fillColor={255,255,255},
        fillPattern=FillPattern.Solid),
      Line(points={{-50,60},{-50,-60},{50,-60},{50,60},{-50,60}}, color={0,0,255}),
      Line(points={{-50,0},{50,0}}, color={0,0,255}, pattern=LinePattern.Dash),
      Text(extent={{-60,40},{60,10}}, textString="H", textColor={0,0,0}),
      Text(extent={{-60,-10},{60,-40}}, textString="u·U", textColor={0,0,255}),
      Text(extent={{-150,140},{150,100}}, textString="%name", textColor={0,0,255})}),
    Documentation(info="<html>
<p>Mostek H z PWM uśredniony w czasie: na silnik trafia napięcie <code>v_mot = u·v_bat</code>,
gdzie <code>u</code> to wypełnienie PWM ze znakiem kierunku. Model pomija przełączanie tranzystorów
(częstotliwość PWM rzędu kHz jest dużo wyższa niż dynamika silnika) i straty w tranzystorach.</p>
<p><b>Zachowanie mocy:</b> skoro mostek jest bezstratny, moc pobierana z baterii równa się mocy oddanej
do silnika, czyli <code>i_bat = u·i_mot</code>. Przy <code>u = 0,3</code> silnik może pobierać 1 A,
a bateria tylko 0,3 A – mostek działa jak przetwornica obniżająca napięcie.
Przy hamowaniu (<code>u·i_mot &lt; 0</code>) energia wraca do baterii.</p>
<p>Wersja z <b>wspólnym biegunem ujemnym</b> (3 piny) pozwala użyć jednej masy dla całego obwodu.
Ujemne <code>u</code> daje ujemne <code>v_mot</code>, czyli odwrotny kierunek obrotów.</p>
</html>"));
end HBridge;
