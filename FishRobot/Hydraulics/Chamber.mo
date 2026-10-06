within FishRobot.Hydraulics;
model Chamber "Komora silikonowa: nieliniowa podatność p = f(V) z tabeli"
  parameter Modelica.Units.SI.AbsolutePressure p_ambient = 1.01325e5
    "Ciśnienie otoczenia (woda wokół komory); krzywa z tabeli to nadciśnienie względem niego";
  parameter Modelica.Units.SI.Volume V_prefill = 5e-6
    "Objętość początkowa (wstępne napełnienie) (PLACEHOLDER – do identyfikacji)";

  parameter Boolean tableOnFile = false "= true: krzywa p–V z pliku (np. CSV z SOFA lub z pomiaru)"
    annotation (Evaluate=true, Dialog(group="Krzywa p–V"), choices(checkBox=true));
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
    annotation (Dialog(group="Krzywa p–V", enable=not tableOnFile));
  parameter String fileName = "NoName" "Plik z krzywą (CSV: V [m3], p [Pa])"
    annotation (Dialog(group="Krzywa p–V", enable=tableOnFile,
      loadSelector(filter="Pliki CSV (*.csv);;Pliki MAT (*.mat)", caption="Krzywa p–V komory")));
  parameter String tableName = "NoName" "Nazwa macierzy (tylko dla plików .mat/.txt)"
    annotation (Dialog(group="Krzywa p–V", enable=tableOnFile));
  parameter Integer nHeaderLines = 1 "Liczba linii nagłówka w CSV"
    annotation (Dialog(group="Krzywa p–V", enable=tableOnFile));

  FishRobot.Interfaces.HydraulicPort_a port
    annotation (Placement(transformation(extent={{-10,-110},{10,-90}})));
  Modelica.Blocks.Interfaces.RealOutput V_out(unit="m3") "Objętość komory (np. do modelu ogona)"
    annotation (Placement(transformation(extent={{100,-10},{120,10}})));

  Modelica.Units.SI.Volume V(start=V_prefill, fixed=true, nominal=1e-5) "Objętość cieczy w komorze";
  Modelica.Units.SI.PressureDifference p_gauge(nominal=1e4) "Nadciśnienie p - p_ambient";
  Modelica.Units.SI.Energy E_elastic(start=0, fixed=true)
    "Energia sprężysta zgromadzona w ściankach (względem stanu początkowego)";

protected
  Modelica.Blocks.Tables.CombiTable1Ds pV(
    final tableOnFile=tableOnFile,
    final table=table,
    final fileName=fileName,
    final tableName=tableName,
    final nHeaderLines=nHeaderLines,
    final columns={2},
    final smoothness=Modelica.Blocks.Types.Smoothness.MonotoneContinuousDerivative1,
    final extrapolation=Modelica.Blocks.Types.Extrapolation.LastTwoPoints)
    "Krzywa p–V: interpolacja monotoniczna z ciągłą pochodną";

equation
  // Ciecz nieściśliwa: zmiana objętości komory = przepływ wpływający przez port.
  der(V) = port.V_flow;
  pV.u = V;
  p_gauge = pV.y[1];
  port.p = p_ambient + p_gauge;
  V_out = V;
  // Moc wpływająca do ścianek = nadciśnienie · przepływ; jej całka to energia sprężysta.
  der(E_elastic) = p_gauge*port.V_flow;

  annotation (
    Icon(graphics={
      Ellipse(extent={{-80,80},{80,-80}}, lineColor={0,0,0}, fillColor={255,170,170},
        fillPattern=FillPattern.Solid),
      Ellipse(extent={{-55,55},{55,-55}}, lineColor={0,128,255}, fillColor={0,128,255},
        fillPattern=FillPattern.Solid),
      Line(points={{0,-80},{0,-90}}, color={0,128,255}),
      Line(points={{80,0},{100,0}}, color={0,0,127}),
      Text(extent={{-150,130},{150,90}}, textString="%name", textColor={0,0,255})}),
    Documentation(info="<html>
<p>Komora z silikonu, która rozszerza się pod ciśnieniem. Ciecz jest nieściśliwa, więc cała
<b>podatność</b> (zdolność do przyjęcia objętości) pochodzi ze ścianek:</p>
<pre>  dV/dt = V_flow            (zachowanie objętości)
  p = p_ambient + f(V)      (krzywa p–V ścianek, z tabeli)</pre>
<p><b>Dlaczego nieliniowa:</b> silikon na początku łatwo się wybrzusza (mała sztywność <i>dp/dV</i>),
a przy dużym rozciągnięciu sztywnieje. Placeholderowa krzywa ma ten kształt. Poniżej objętości
spoczynkowej (5 ml) ciśnienie spada, bo komora jest zasysana i zaczyna się zapadać.</p>
<p><b>Sztywność</b> <i>k = dp/dV</i> razem z oporem przewodów i bezwładnością ogona wyznacza pasmo
układu: sztywniejsza komora reaguje szybciej, ale przy tej samej objętości wymaga wyższego ciśnienia.</p>
<p><b>Podmiana krzywej:</b> ustaw <code>tableOnFile = true</code> i wskaż plik CSV z dwiema kolumnami
<code>V [m3], p - p_ambient [Pa]</code> (jedna linia nagłówka). Tak podłączysz krzywą z demo SOFA
albo z pomiaru na stole. Krzywa musi być <b>rosnąca</b>; interpolacja monotoniczna
(<code>MonotoneContinuousDerivative1</code>) zachowuje tę cechę i ma ciągłą pochodną, więc solver
nie widzi „załamań” w punktach tabeli. Poza zakresem tabeli krzywa jest przedłużana liniowo.</p>
<p><b>Energia:</b> <code>E_elastic = &int; p_gauge·dV</code> – praca włożona w odkształcenie ścianek.
Dla ścianek idealnie sprężystych da się ją w całości odzyskać (nie jest stratą).</p>
</html>"));
end Chamber;
