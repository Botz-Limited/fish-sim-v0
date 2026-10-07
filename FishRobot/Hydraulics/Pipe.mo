within FishRobot.Hydraulics;
model Pipe "Przewód: tarcie laminarne lub turbulentne + straty miejscowe, opcjonalnie inertancja słupa cieczy"
  extends FishRobot.Interfaces.PartialTwoPort;
  import Modelica.Constants.pi;

  parameter Modelica.Units.SI.Length l = 0.2 "Długość przewodu (PLACEHOLDER – do identyfikacji)";
  parameter Modelica.Units.SI.Diameter d = 4e-3 "Średnica wewnętrzna (PLACEHOLDER – do identyfikacji)";
  parameter Real zeta(min=0) = 1.5 "Współczynnik strat miejscowych (kolana, złączki) (PLACEHOLDER – do identyfikacji)";
  parameter Modelica.Units.SI.Density rho = 998.2 "Gęstość wody (ok. 20 °C)";
  parameter Modelica.Units.SI.DynamicViscosity mu = 1.002e-3 "Lepkość dynamiczna wody (ok. 20 °C)";
  parameter Boolean useTurbulent = true
    "= true: powyżej Re = Re_lam tarcie przechodzi w turbulentne (Haaland); = false: zawsze Hagen–Poiseuille"
    annotation (Evaluate=true, choices(checkBox=true));
  parameter Modelica.Units.SI.Length roughness = 2.5e-5
    "Chropowatość bezwzględna ścianki (jak domyślnie w Modelica.Fluid) (PLACEHOLDER – do identyfikacji)"
    annotation (Dialog(enable=useTurbulent));
  parameter Real Re_lam = 2000 "Koniec zakresu laminarnego" annotation (Dialog(enable=useTurbulent));
  parameter Real Re_turb = 4000 "Początek zakresu w pełni turbulentnego" annotation (Dialog(enable=useTurbulent));
  parameter Boolean useInertance = false "= true: uwzględnij bezwładność słupa cieczy (V_flow staje się stanem)"
    annotation (Evaluate=true, choices(checkBox=true));
  parameter Modelica.Units.SI.VolumeFlowRate V_flow_small = 1e-8
    "Próg regularyzacji członu |V|·V (dużo mniejszy od typowych przepływów)";
  parameter Modelica.Units.SI.VolumeFlowRate V_flow_start = 0 "Przepływ początkowy (tylko gdy useInertance)"
    annotation (Dialog(enable=useInertance));

  final parameter Modelica.Units.SI.Area A = pi*d^2/4 "Pole przekroju";
  final parameter Real R_lam(unit="Pa.s/m3") = 128*mu*l/(pi*d^4) "Opór laminarny (Hagen–Poiseuille)";
  final parameter Real R_local(unit="Pa.s2/m6") = zeta*rho/(2*A^2) "Współczynnik strat miejscowych (kwadratowych)";
  final parameter Real R_wall(unit="Pa.s2/m6") = l/d*rho/(2*A^2)
    "Tarcie turbulentne: dp = lambda·R_wall·|V|·V (wzór Darcy’ego–Weisbacha)";
  final parameter Real L_inert(unit="Pa.s2/m3") = rho*l/A "Inertancja słupa cieczy";

  Modelica.Units.SI.PressureDifference dp_loss "Spadek ciśnienia na tarciu i stratach miejscowych";
  Modelica.Units.SI.Power P_loss "Moc rozpraszana (zamieniana w ciepło)";
  Modelica.Units.SI.Velocity v "Średnia prędkość cieczy";
  Real Re "Liczba Reynoldsa (laminarny gdy Re < ok. 2300)";
  Modelica.Units.SI.PressureDifference dp_wall "Spadek ciśnienia na tarciu o ścianki";
  Real lambda_turb "Współczynnik tarcia turbulentnego (Haaland)";
  Real w_turb "Udział tarcia turbulentnego: 0 laminarnie, 1 turbulentnie";
protected
  Real x_turb "Położenie w zakresie przejściowym (0 przy Re_lam, 1 przy Re_turb)";
public

equation
  // Regularyzacja: V·sqrt(V² + V_small²) ≈ |V|·V dla |V| >> V_small, ale jest gładka w zerze.
  // Wersja z abs() ma nieciągłą drugą pochodną w zerze, co zmusza solver do bardzo małych kroków
  // przy każdej zmianie kierunku przepływu (a w ogonie ryby przepływ zmienia kierunek co półokres).
  if useTurbulent then
    // Haaland: jawne przybliżenie równania Colebrooka (różnica < 2%). Re liczone z regularyzowanym |V|,
    // żeby logarytm był określony także przy V = 0 (wtedy i tak w_turb = 0).
    lambda_turb = (-1.8*log10((roughness/d/3.7)^1.11
      + 6.9*mu*A/(rho*d*sqrt(V_flow^2 + V_flow_small^2))))^(-2);
    // Gładkie przejście (wielomian 3x² − 2x³) między Re_lam a Re_turb, bez zdarzeń.
    x_turb = noEvent(min(1, max(0, (Re - Re_lam)/(Re_turb - Re_lam))));
    w_turb = x_turb^2*(3 - 2*x_turb);
  else
    lambda_turb = 0;
    x_turb = 0;
    w_turb = 0;
  end if;
  dp_wall = (1 - w_turb)*R_lam*V_flow + w_turb*lambda_turb*R_wall*V_flow*sqrt(V_flow^2 + V_flow_small^2);
  dp_loss = dp_wall + R_local*V_flow*sqrt(V_flow^2 + V_flow_small^2);
  if useInertance then
    // Różnica ciśnień, której nie zjada tarcie, przyspiesza słup cieczy o masie rho·A·l.
    L_inert*der(V_flow) = dp - dp_loss;
  else
    dp = dp_loss;
  end if;
  P_loss = dp_loss*V_flow;
  v = V_flow/A;
  Re = rho*abs(v)*d/mu;

initial equation
  if useInertance then
    V_flow = V_flow_start;
  end if;

  annotation (
    Icon(graphics={
      Rectangle(extent={{-90,20},{90,-20}}, lineColor={0,0,0}, fillColor={0,128,255},
        fillPattern=FillPattern.HorizontalCylinder),
      Text(extent={{-150,70},{150,30}}, textString="%name", textColor={0,0,255})}),
    Documentation(info="<html>
<p>Spadek ciśnienia w przewodzie o długości <i>l</i> i średnicy <i>d</i>:</p>
<pre>  dp_loss = dp_wall + R_local·|V_flow|·V_flow
  dp_wall = (1 - w)·R_lam·V_flow + w·&lambda;_turb·R_wall·|V_flow|·V_flow</pre>
<ul>
<li><b>Tarcie laminarne</b> (prawo Hagena–Poiseuille’a): <code>R_lam = 128·&mu;·l / (&pi;·d<sup>4</sup>)</code>.
Wynika z paraboliczego profilu prędkości w rurze kołowej. Zauważ <i>d<sup>4</sup></i>: dwa razy węższa rura
to 16 razy większy opór.</li>
<li><b>Tarcie turbulentne</b> (<code>useTurbulent = true</code>): wzór Darcy’ego–Weisbacha
<code>dp = &lambda;·(l/d)·&rho;·v<sup>2</sup>/2</code>, stąd <code>R_wall = (l/d)·&rho; / (2·A<sup>2</sup>)</code>.
Współczynnik tarcia z wzoru Haalanda (jawne przybliżenie Colebrooka):
<code>1/&radic;&lambda; = -1,8·log<sub>10</sub>((&epsilon;/d / 3,7)<sup>1,11</sup> + 6,9/Re)</code>.</li>
<li><b>Przejście</b>: przepływ w rurze przestaje być laminarny w okolicy Re &asymp; 2300. Waga <code>w</code> rośnie
gładko (wielomian <code>3x<sup>2</sup> - 2x<sup>3</sup></code>) od 0 przy <code>Re_lam = 2000</code> do 1 przy
<code>Re_turb = 4000</code>, tak jak w <code>Modelica.Fluid</code> (<code>WallFriction.Detailed</code>).
Przy Re = 4000 opór turbulentny jest ok. 3 razy większy niż laminarny, więc pominięcie przejścia mocno
zaniża straty przy szybkim pompowaniu.</li>
<li><b>Straty miejscowe</b> (kolana, złączki): <code>dp = &zeta;·&rho;·v<sup>2</sup>/2</code>, gdzie
<code>v = V_flow/A</code>, stąd <code>R_local = &zeta;·&rho; / (2·A<sup>2</sup>)</code>.</li>
</ul>
<p><b>Regularyzacja:</b> zamiast <code>|V|·V</code> używamy <code>V·sqrt(V<sup>2</sup> + V_small<sup>2</sup>)</code>.
Dla <code>|V| = 10·V_small</code> błąd względny wynosi ok. 0,5%, dla większych przepływów jest pomijalny.
Funkcja jest gładka (różniczkowalna dowolnie wiele razy), więc solver nie musi zwalniać przy zmianie kierunku przepływu.</p>
<p><b>Inertancja</b> (<code>useInertance = true</code>): słup cieczy ma masę <code>&rho;·A·l</code>; z II zasady Newtona
dla słupa: <code>L·dV_flow/dt = dp - dp_loss</code>, <code>L = &rho;·l/A</code>. Przy samej części laminarnej
przepływ narasta wykładniczo ze stałą czasową <code>&tau; = L/R_lam</code>.
Nie łącz rury z inertancją szeregowo ze źródłem wymuszającym przepływ – wtedy pochodna przepływu
byłaby narzucona z zewnątrz (problem wysokiego indeksu).</p>
<p>Moc rozpraszana: <code>P_loss = dp_loss·V_flow &ge; 0</code>. Z inertancją część mocy <code>dp·V_flow</code>
trafia do energii kinetycznej słupa <code>L·V_flow<sup>2</sup>/2</code>.</p>
<p>Wzór Hagena–Poiseuille’a obowiązuje dla <code>Re &lt; ok. 2300</code>; <code>Re</code> jest liczone, żeby można to sprawdzić na wykresie.</p>
</html>"));
end Pipe;
