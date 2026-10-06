within FishRobot.Buoyancy;
model VerticalDynamics "Ruch pionowy: (m + m_added_z)·z'' = ρ·g·(V_hull + V_b) - m·g - ½·ρ·C_dz·A_z·|z'|·z'"
  parameter Modelica.Units.SI.Mass m = 1.0 "Masa ryby (PLACEHOLDER – do identyfikacji)";
  parameter Modelica.Units.SI.Mass m_added_z = 0.5 "Masa dodana w pionie (PLACEHOLDER – do identyfikacji)";
  parameter Modelica.Units.SI.Volume V_b_neutral = 6e-6
    "Objętość pęcherza dająca pływalność neutralną przy powierzchni (projektowa) (PLACEHOLDER – do identyfikacji)";
  parameter Modelica.Units.SI.Density rho = 998.2 "Gęstość wody";
  parameter Real C_dz = 1.0 "Współczynnik oporu w pionie (PLACEHOLDER – do identyfikacji)";
  parameter Modelica.Units.SI.Area A_z = 0.02 "Pole rzutu z góry (PLACEHOLDER – do identyfikacji)";
  parameter Modelica.Units.SI.Velocity v_small = 1e-4 "Próg regularyzacji |v|";
  parameter Boolean useCompressibility = false
    "= true: kieszeń powietrza w kadłubie ściska się z głębokością (prawo Boyle’a)"
    annotation (Evaluate=true, choices(checkBox=true));
  parameter Modelica.Units.SI.Volume V_air0 = 20e-6
    "Objętość powietrza w kadłubie przy powierzchni (PLACEHOLDER – do identyfikacji)"
    annotation (Dialog(enable=useCompressibility));
  parameter Modelica.Units.SI.AbsolutePressure p_atm = 1.01325e5 "Ciśnienie atmosferyczne";
  parameter Modelica.Units.SI.Position z_start = -0.5 "Położenie początkowe (z < 0 pod wodą)";
  parameter Modelica.Units.SI.Velocity v_start = 0 "Prędkość początkowa";

  final parameter Modelica.Units.SI.Volume V_hull = m/rho - V_b_neutral
    "Objętość kadłuba (bez pęcherza), dobrana tak, by przy V_b = V_b_neutral wyporność = ciężar";

  Modelica.Blocks.Interfaces.RealInput V_b(unit="m3") "Objętość pęcherza ze strzykawki"
    annotation (Placement(transformation(extent={{-140,-20},{-100,20}})));
  Modelica.Blocks.Interfaces.RealOutput z(unit="m") "Położenie pionowe (0 = powierzchnia, ujemne = pod wodą)"
    annotation (Placement(transformation(extent={{100,30},{120,50}})));
  Modelica.Blocks.Interfaces.RealOutput v_z(unit="m/s") "Prędkość pionowa (dodatnia = wynurzanie)"
    annotation (Placement(transformation(extent={{100,-50},{120,-30}})));

  Modelica.Units.SI.Volume V_air "Aktualna objętość kieszeni powietrza";
  Modelica.Units.SI.Force F_buoy "Siła wyporu";
  Modelica.Units.SI.Force F_net_static "Wypór - ciężar (bez oporu)";
  Modelica.Units.SI.Force F_drag "Opór wody";
equation
  // Prawo Boyle’a: p·V = const; ciśnienie rośnie o ρ·g na każdy metr głębokości.
  V_air = if useCompressibility then V_air0*p_atm/(p_atm + rho*Modelica.Constants.g_n*noEvent(max(0, -z)))
          else V_air0;
  F_buoy = rho*Modelica.Constants.g_n*(V_hull - V_air0 + V_air + V_b);
  F_net_static = F_buoy - m*Modelica.Constants.g_n;
  F_drag = 0.5*rho*C_dz*A_z*v_z*sqrt(v_z^2 + v_small^2);
  assert(z < 0.02, "VerticalDynamics: ryba wynurzyła się ponad powierzchnię (z > 0) – model tego nie obejmuje",
    AssertionLevel.warning);
  der(z) = v_z;
  (m + m_added_z)*der(v_z) = F_net_static - F_drag;
initial equation
  z = z_start;
  v_z = v_start;
  annotation (
    Icon(graphics={
      Rectangle(extent={{-100,100},{100,-100}}, lineColor={0,0,0}, fillColor={170,213,255},
        fillPattern=FillPattern.Solid),
      Ellipse(extent={{-50,20},{50,-20}}, lineColor={0,0,0}, fillColor={255,170,85},
        fillPattern=FillPattern.Solid),
      Line(points={{0,30},{0,80}}, arrow={Arrow.None, Arrow.Filled}),
      Line(points={{0,-30},{0,-80}}, arrow={Arrow.None, Arrow.Filled}),
      Text(extent={{-150,150},{150,110}}, textString="%name", textColor={0,0,255})}),
    Documentation(info="<html>
<p>Ryba jako punkt materialny poruszający się w pionie:</p>
<pre>  (m + m_added_z)·z'' = &rho;·g·(V_hull + V_b) - m·g - &frac12;·&rho;·C_dz·A_z·|z'|·z'</pre>
<p><b>Pływalność neutralna:</b> wypór równoważy ciężar, gdy <code>V_hull + V_b = m/&rho;</code>. Kadłub jest dobrany tak,
by działo się to przy <code>V_b = V_b_neutral</code>. Każdy mililitr ponad to daje ok. 0,01 N siły w górę.
To mało, ale opór przy małych prędkościach też jest mały – stąd prędkości rzędu centymetrów na sekundę.</p>
<p><b>Ściśliwość (przełącznik <code>useCompressibility</code>):</b> jeśli w kadłubie jest pęcherzyk powietrza, to na głębokości
ciśnienie go ściska (<code>V = V_0·p_atm/(p_atm + &rho;·g·h)</code>), wypór maleje i ryba tonie szybciej. Gdy się wynurza,
powietrze się rozpręża i ryba wypływa jeszcze szybciej. <b>Równowaga jest niestabilna</b>: każde odchylenie samo się
pogłębia. Dlatego okręty podwodne i ryby z balastem potrzebują aktywnej regulacji głębokości albo kadłuba
bez ściśliwych przestrzeni. Test <code>BallastStatics</code> pokazuje to porównaniem obu wariantów.</p>
<p>Pominięto: sprzężenie z ruchem do przodu i z ogonem, siłę nośną od kształtu, wynurzenie ponad powierzchnię (model
zakłada <code>z &lt; 0</code>).</p>
</html>"));
end VerticalDynamics;
