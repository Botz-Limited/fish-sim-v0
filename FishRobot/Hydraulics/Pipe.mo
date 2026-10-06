within FishRobot.Hydraulics;
model Pipe "Przewód: strata laminarno-turbulentna, opcjonalnie inertancja słupa cieczy"
  extends FishRobot.Interfaces.PartialTwoPort;
  import Modelica.Constants.pi;

  parameter Modelica.Units.SI.Length l = 0.2 "Długość przewodu (PLACEHOLDER – do identyfikacji)";
  parameter Modelica.Units.SI.Diameter d = 4e-3 "Średnica wewnętrzna (PLACEHOLDER – do identyfikacji)";
  parameter Real zeta(min=0) = 1.5 "Współczynnik strat miejscowych (kolana, złączki) (PLACEHOLDER – do identyfikacji)";
  parameter Modelica.Units.SI.Density rho = 998.2 "Gęstość wody (ok. 20 °C)";
  parameter Modelica.Units.SI.DynamicViscosity mu = 1.002e-3 "Lepkość dynamiczna wody (ok. 20 °C)";
  parameter Boolean useInertance = false "= true: uwzględnij bezwładność słupa cieczy (V_flow staje się stanem)"
    annotation (Evaluate=true, choices(checkBox=true));
  parameter Modelica.Units.SI.VolumeFlowRate V_flow_small = 1e-8
    "Próg regularyzacji członu |V|·V (dużo mniejszy od typowych przepływów)";
  parameter Modelica.Units.SI.VolumeFlowRate V_flow_start = 0 "Przepływ początkowy (tylko gdy useInertance)"
    annotation (Dialog(enable=useInertance));

  final parameter Modelica.Units.SI.Area A = pi*d^2/4 "Pole przekroju";
  final parameter Real R_lam(unit="Pa.s/m3") = 128*mu*l/(pi*d^4) "Opór laminarny (Hagen–Poiseuille)";
  final parameter Real R_turb(unit="Pa.s2/m6") = zeta*rho/(2*A^2) "Współczynnik straty kwadratowej";
  final parameter Real L_inert(unit="Pa.s2/m3") = rho*l/A "Inertancja słupa cieczy";

  Modelica.Units.SI.PressureDifference dp_loss "Spadek ciśnienia na tarciu i stratach miejscowych";
  Modelica.Units.SI.Power P_loss "Moc rozpraszana (zamieniana w ciepło)";
  Modelica.Units.SI.Velocity v "Średnia prędkość cieczy";
  Real Re "Liczba Reynoldsa (laminarny gdy Re < ok. 2300)";

equation
  // Regularyzacja: V·sqrt(V² + V_small²) ≈ |V|·V dla |V| >> V_small, ale jest gładka w zerze.
  // Wersja z abs() ma nieciągłą drugą pochodną w zerze, co zmusza solver do bardzo małych kroków
  // przy każdej zmianie kierunku przepływu (a w ogonie ryby przepływ zmienia kierunek co półokres).
  dp_loss = R_lam*V_flow + R_turb*V_flow*sqrt(V_flow^2 + V_flow_small^2);
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
<pre>  dp_loss = R_lam·V_flow + R_turb·|V_flow|·V_flow</pre>
<ul>
<li><b>Część laminarna</b> (prawo Hagena–Poiseuille’a): <code>R_lam = 128·&mu;·l / (&pi;·d<sup>4</sup>)</code>.
Wynika z paraboliczego profilu prędkości w rurze kołowej. Zauważ <i>d<sup>4</sup></i>: dwa razy węższa rura
to 16 razy większy opór.</li>
<li><b>Część kwadratowa</b> (straty miejscowe): <code>dp = &zeta;·&rho;·v<sup>2</sup>/2</code>, gdzie
<code>v = V_flow/A</code>, stąd <code>R_turb = &zeta;·&rho; / (2·A<sup>2</sup>)</code>.</li>
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
<p>Wzór Hagena–Poiseuille’a obowiązuje dla <code>Re &lt; ok. 2300</code>. Powyżej model jest tylko przybliżeniem;
<code>Re</code> jest liczone, żeby można to sprawdzić na wykresie.</p>
</html>"));
end Pipe;
