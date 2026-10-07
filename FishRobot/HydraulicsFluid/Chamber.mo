within FishRobot.HydraulicsFluid;
model Chamber "Komora o podatnych ściankach (p = f(V)) na bazie naczynia z Modelica.Fluid"
  extends Modelica.Fluid.Vessels.BaseClasses.PartialLumpedVessel(
    final fluidVolume = V,
    final nPorts = 1,
    final use_portsData = false,
    final use_HeatTransfer = false,
    heatTransfer(surfaceAreas={4*Modelica.Constants.pi*(3/4*V_prefill/Modelica.Constants.pi)^(2/3)}),
    p_start = p_ambient);
  // Pole powierzchni jest wymagane przez model wymiany ciepła, choć ten jest wyłączony
  // (use_HeatTransfer = false: ścianki adiabatyczne).

  parameter Modelica.Units.SI.AbsolutePressure p_ambient = 1.01325e5
    "Ciśnienie otoczenia (woda wokół komory); krzywa z tabeli to nadciśnienie względem niego";
  parameter Modelica.Units.SI.Volume V_prefill = 5e-6
    "Objętość początkowa (wstępne napełnienie) (PLACEHOLDER – do identyfikacji)";
  // Ta sama placeholderowa krzywa co w Hydraulics.Chamber (zmieniając jedną, zmień drugą).
  parameter Real table[:, 2] = [
       0.0e-6, -20e3;
       2.0e-6,  -5e3;
       4.0e-6,  -1e3;
       5.0e-6,     0;
       6.0e-6,   2e3;
       8.0e-6,   6e3;
      10.0e-6,  12e3;
      12.0e-6,  22e3;
      14.0e-6,  38e3;
      16.0e-6,  62e3;
      20.0e-6, 140e3]
    "Kolumny: V [m3], nadciśnienie p - p_ambient [Pa] (PLACEHOLDER – do identyfikacji)"
    annotation (Dialog(group="Krzywa p–V"));

  // StateSelect.always: stanem jest objętość, a ciśnienie liczy się z krzywej. Bez tego solver
  // wybrałby ciśnienie (medium.p ma preferowany stan) i musiałby co krok odwracać tabelę p–V.
  Modelica.Units.SI.Volume V(start=V_prefill, fixed=true, nominal=1e-5, stateSelect=StateSelect.always)
    "Objętość cieczy w komorze";
  Modelica.Units.SI.PressureDifference p_gauge(nominal=1e4) "Nadciśnienie p - p_ambient";

protected
  Modelica.Blocks.Tables.CombiTable1Ds pV(
    final table=table,
    final columns={2},
    final smoothness=Modelica.Blocks.Types.Smoothness.MonotoneContinuousDerivative1,
    final extrapolation=Modelica.Blocks.Types.Extrapolation.LastTwoPoints)
    "Krzywa p–V: interpolacja monotoniczna z ciągłą pochodną";

equation
  pV.u = V;
  p_gauge = pV.y[1];
  medium.p = p_ambient + p_gauge;
  // Praca ścianek nad cieczą: rozszerzająca się komora odbiera cieczy p·dV/dt.
  Wb_flow = -medium.p*der(V);
  vessel_ps_static[1] = medium.p;
  // Bilans masy der(m) = Σ m_flow i m = V·ρ są w klasie bazowej; przy stałej gęstości
  // wynika z nich dokładnie to samo co w Hydraulics.Chamber: dV/dt = V_flow.

  annotation (
    Icon(coordinateSystem(extent={{-100,-100},{100,100}}), graphics={
      Ellipse(extent={{-80,80},{80,-80}}, lineColor={0,0,0}, fillColor={255,170,170},
        fillPattern=FillPattern.Solid),
      Ellipse(extent={{-55,55},{55,-55}}, lineColor={0,127,255}, fillColor={0,127,255},
        fillPattern=FillPattern.Solid),
      Line(points={{0,-80},{0,-100}}, color={0,127,255}),
      Text(extent={{-150,130},{150,90}}, textString="%name", textColor={0,0,255})}),
    Documentation(info="<html>
<p>Naczynia z <code>Modelica.Fluid.Vessels</code> mają stałą objętość (<code>ClosedVolume</code>) albo swobodne
lustro cieczy (<code>OpenTank</code>). Przy cieczy nieściśliwej w zamkniętym obwodzie stała objętość oznacza,
że przepływ nie ma dokąd pójść, a ciśnienie jest nieokreślone. Komora musi więc mieć <b>zmienną objętość</b>.</p>
<p>Bazą jest <code>PartialLumpedVessel</code>: bilans masy <code>der(m) = &Sigma; m_flow</code>, bilans energii
<code>der(U) = H_flow + Q_flow + W_flow</code> i obsługa portów. Dopisujemy objętość jako stan,
krzywą p–V (ta sama tabela co w <code>Hydraulics.Chamber</code>) i pracę ścianek
<code>W_flow = -p·dV/dt</code>.</p>
<p>Dodatkowym stanem jest tu temperatura cieczy w komorze, której lekki pakiet w ogóle nie liczy.</p>
</html>"));
end Chamber;
