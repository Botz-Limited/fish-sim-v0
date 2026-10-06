within FishRobot.Propulsion;
model LighthillFin "Ciąg płetwy ogonowej: model reaktywny Lighthilla (PLACEHOLDER – najsłabsze ogniwo modelu)"
  import Modelica.Constants.pi;
  parameter Modelica.Units.SI.Length L_tail = 0.1
    "Odległość osi ogona od krawędzi spływu płetwy (ustaw jak w TailEquivalent) (PLACEHOLDER – do identyfikacji)";
  parameter Modelica.Units.SI.Length s_fin = 0.06 "Rozpiętość płetwy na krawędzi spływu (PLACEHOLDER – do identyfikacji)";
  parameter Real C_T = 1.0
    "Współczynnik korekcyjny (1 = czysta teoria Lighthilla) (PLACEHOLDER – do identyfikacji z pomiaru ciągu na uwięzi)";
  parameter Modelica.Units.SI.Density rho = 998.2 "Gęstość wody";
  final parameter Real m_a(unit="kg/m") = C_T*rho*pi*s_fin^2/4
    "Masa dodana na jednostkę długości na krawędzi spływu: ρ·π·s²/4 (razy C_T)";

  Modelica.Mechanics.Rotational.Interfaces.Flange_a flange "Oś ogona (kąt θ względem kadłuba)"
    annotation (Placement(transformation(extent={{-110,-10},{-90,10}})));
  Modelica.Blocks.Interfaces.RealInput U(unit="m/s") "Prędkość pływania do przodu"
    annotation (Placement(transformation(extent={{-20,-20},{20,20}}, rotation=90, origin={0,-120})));
  Modelica.Blocks.Interfaces.RealOutput T(unit="N") "Ciąg (dodatni = do przodu)"
    annotation (Placement(transformation(extent={{100,-10},{120,10}})));

  Modelica.Units.SI.Angle theta "Kąt ogona";
  Modelica.Units.SI.AngularVelocity w "Prędkość kątowa ogona";
  Modelica.Units.SI.Velocity v_tip = L_tail*w "Prędkość boczna krawędzi spływu";
  Modelica.Units.SI.Velocity w_n "Prędkość wody względem płetwy, prostopadle do niej: L·θ' + U·θ";
  Modelica.Units.SI.Power P_fin "Moc pobrana z ogona przez wodę (= T·U + P_wake)";
  Modelica.Units.SI.Power P_thrust = T*U "Moc użyteczna: ciąg razy prędkość";
  Modelica.Units.SI.Power P_wake "Moc zostawiona w śladzie wirowym (zawsze >= 0)";
equation
  theta = flange.phi;
  w = der(theta);
  w_n = L_tail*w + U*theta;
  // Siła boczna m_a·U·w_n na krawędzi spływu, przeniesiona na oś ogona ramieniem L_tail.
  // Działa przeciwnie do ruchu: tłumienie (człon z θ') i sprężyna "wiatrowskazu" (człon z θ).
  flange.tau = m_a*U*L_tail*w_n;
  T = 0.5*m_a*(v_tip^2 - (U*theta)^2);
  P_fin = flange.tau*w;
  P_wake = 0.5*m_a*U*w_n^2;
  annotation (
    Icon(graphics={
      Rectangle(extent={{-90,90},{90,-90}}, lineColor={0,0,0}, fillColor={255,255,255},
        fillPattern=FillPattern.Solid),
      Polygon(points={{-80,0},{-20,10},{20,50},{10,0},{20,-50},{-20,-10},{-80,0}}, lineColor={0,0,0},
        fillColor={255,170,85}, fillPattern=FillPattern.Solid),
      Line(points={{30,0},{80,0}}, color={0,0,127}, thickness=0.5, arrow={Arrow.None, Arrow.Filled}),
      Text(extent={{30,40},{90,10}}, textString="T", textColor={0,0,127}),
      Text(extent={{-150,140},{150,100}}, textString="%name", textColor={0,0,255})}),
    Documentation(info="<html>
<p><b>Uwaga: to najsłabsze ogniwo całego modelu.</b> Ciąg płetwy zależy od przepływu przestrzennego, wirów i
odkształcenia płetwy, a tego model 1D nie widzi. Poniższy wzór to <b>placeholderowy model empiryczny</b> o
uzasadnionej fizycznie postaci. Jego parametry (<code>s_fin</code>, <code>C_T</code>) trzeba wyznaczyć z pomiaru ciągu
na uwięzi albo z demo CFD/MuJoCo, zanim wyciągnie się wnioski o prędkości pływania.</p>

<p><b>Postać: teoria wydłużonego ciała Lighthilla (1970)</b>, zastosowana do sztywnej płetwy o długości
<code>L</code> obracającej się o kąt &theta;. Krawędź spływu porusza się na boki z prędkością <code>h' = L·&theta;'</code>
i jest nachylona pod kątem &theta; do kierunku płynięcia. Woda przy krawędzi ma względem płetwy prędkość
prostopadłą</p>
<pre>  w = L·&theta;' + U·&theta;</pre>
<p>Płetwa rozpędza na boki wodę o masie dodanej <code>m_a = &rho;·&pi;·s<sup>2</sup>/4</code> na metr. Z bilansu pędu wychodzą
trzy moce:</p>
<pre>  P_fin   = m_a·U·w·L·&theta;'                    moc pobrana z ogona
  T       = &frac12;·m_a·((L·&theta;')<sup>2</sup> - U<sup>2</sup>·&theta;<sup>2</sup>)       ciąg
  P_wake  = &frac12;·m_a·U·w<sup>2</sup>                      energia zostawiona w śladzie</pre>
<p>Tożsamość <code>P_fin = T·U + P_wake</code> zachodzi <b>dokładnie w każdej chwili</b> (sprawdź, rozpisując
<code>w<sup>2</sup></code>). Dlatego model jest energetycznie spójny: ciąg nie bierze się znikąd, tylko z momentu
<code>&tau; = m_a·U·L·w</code>, który hamuje ogon. Ten moment działa przez złącze <code>flange</code>, więc bilans
energii w <code>TailDrive</code> widzi go automatycznie.</p>

<p><b>Wnioski z tej postaci</b> (dla sinusa &theta; = &Theta;·sin &omega;t):</p>
<ul>
<li>średni ciąg <code>T = &frac14;·m_a·&Theta;<sup>2</sup>·(L<sup>2</sup>&omega;<sup>2</sup> - U<sup>2</sup>)</code> – rośnie z kwadratem
prędkości końcówki ogona, czyli z kwadratem iloczynu &Theta;·f,</li>
<li>ciąg znika przy <code>U = L·&omega;</code> – ryba nie popłynie szybciej niż krawędź spływu się „przesuwa”,</li>
<li>sprawność napędu <code>&eta; = T·U/P_fin = &frac12;·(1 - (U/L&omega;)<sup>2</sup>)</code> – sztywna płetwa obracana
w jednym przegubie ma najwyżej 50%. Prawdziwe ryby wyginają całe ciało falą i osiągają więcej.</li>
</ul>

<p>Ograniczenia: wzór Lighthilla dotyczy średnich po okresie, tu stosujemy go chwilowo (ciąg chwilami bywa
ujemny – to normalne). Przy <code>U = 0</code> moment znika, a ciąg nie – teoria nie opisuje ciągu na uwięzi.
Opór poprzeczny płetwy jest osobno w <code>TailEquivalent</code> (<code>c_h</code>), a masa dodana ogona to
<code>J_added</code>.</p>
</html>"));
end LighthillFin;
