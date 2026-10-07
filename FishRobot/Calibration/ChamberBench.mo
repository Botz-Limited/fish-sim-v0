within FishRobot.Calibration;
model ChamberBench "Stanowisko: strzykawka wtłacza i wyciąga wodę z komory, ogon zablokowany (krok 5)"
  extends Modelica.Icons.Example;
  import Modelica.Constants.pi;

  parameter String fileName = Modelica.Utilities.Files.loadResource(
    "modelica://FishRobot/Resources/Data/chamber_pV_placeholder.csv") "Krzywa p–V do sprawdzenia (CSV: V [m3], p [Pa])";
  parameter Modelica.Units.SI.Volume V_min = 2e-6 "Najmniejsza objętość w cyklu strzykawki";
  parameter Modelica.Units.SI.Volume V_max = 16e-6 "Największa objętość w cyklu strzykawki";
  parameter Modelica.Units.SI.Time T = 1 "Okres cyklu (quasi-statycznie: bez przewodu nie ma to znaczenia)";

  Modelica.Blocks.Sources.Sine syringe(amplitude=(V_max - V_min)/2*2*pi/T, f=1/T) "Przepływ ze strzykawki"
    annotation (Placement(transformation(extent={{-80,-10},{-60,10}})));
  FishRobot.Hydraulics.VolumeFlowSource source
    annotation (Placement(transformation(extent={{-40,-10},{-20,10}})));
  FishRobot.Hydraulics.Chamber chamber(V_prefill=V_min, tableOnFile=true, fileName=fileName)
    annotation (Placement(transformation(extent={{0,-10},{20,10}})));

  Modelica.Units.SI.Volume V = chamber.V "Objętość komory";
  Modelica.Units.SI.PressureDifference p = chamber.p_gauge "Nadciśnienie w komorze";
equation
  connect(syringe.y, source.V_flow) annotation (Line(points={{-59,0},{-42,0}}, color={0,0,127}));
  connect(source.port, chamber.port) annotation (Line(points={{-20,0},{10,0},{10,-10}}, color={0,128,255}));
  annotation (
    experiment(StopTime=0.5, Interval=1e-3, Tolerance=1e-8),
    Documentation(info="<html>
<p>Sprawdza krzywą p–V wyznaczoną z pomiaru: komora z <code>tableOnFile = true</code> przechodzi od
<code>V_min</code> do <code>V_max</code> (pół okresu sinusa przepływu). Wynik powinien leżeć na punktach
krzywej z pliku, a między nimi interpolacja monotoniczna nie może tworzyć garbów.</p>
<p>Na prawdziwym stole strzykawka (np. pompa strzykawkowa) przesuwa się powoli, w kilku cyklach
napełnij–opróżnij, a czujnik ciśnienia jest przy komorze. Komora silikonowa ma histerezę, której model
nie ma: <code>calibrate.py chamber</code> uśrednia gałąź napełniania i opróżniania i liczy pole pętli.</p>
</html>"));
end ChamberBench;
