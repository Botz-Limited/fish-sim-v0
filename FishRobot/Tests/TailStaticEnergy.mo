within FishRobot.Tests;
model TailStaticEnergy "Test: ogon pod skokiem różnicy ciśnień – kąt statyczny i bilans energii"
  extends Modelica.Icons.Example;
  parameter Modelica.Units.SI.PressureDifference dp_step = 30e3 "Skok p_L - p_R";

  Modelica.Blocks.Sources.Step step(height=dp_step, offset=1.01325e5, startTime=0.1)
    annotation (Placement(transformation(extent={{-90,30},{-70,50}})));
  FishRobot.Hydraulics.Reservoir resL(use_p_in=true)
    annotation (Placement(transformation(extent={{-60,30},{-40,50}})));
  FishRobot.Hydraulics.Reservoir resR
    annotation (Placement(transformation(extent={{-60,-50},{-40,-30}})));
  FishRobot.Tail.TailEquivalent tail
    annotation (Placement(transformation(extent={{0,-10},{20,10}})));

  parameter Modelica.Units.SI.Angle theta_analytic = tail.D_tail*dp_step/tail.k
    "Kąt statyczny: D_tail·Δp = k·θ";
  Modelica.Units.SI.Energy E_hyd(start=0, fixed=true) "Energia hydrauliczna dostarczona";
  Modelica.Units.SI.Energy E_water(start=0, fixed=true) "Energia rozproszona";
  Modelica.Units.SI.Energy E_balance_error = E_hyd - (tail.E_kin + tail.E_spring + E_water)
    "Powinno być 0";
equation
  der(E_hyd) = tail.P_hyd;
  der(E_water) = tail.P_water;
  connect(step.y, resL.p_in) annotation (Line(points={{-69,40},{-64,40}}, color={0,0,127}));
  connect(resL.port, tail.port_L) annotation (Line(points={{-40,40},{-20,40},{-20,4},{0,4}}, color={0,128,255}));
  connect(resR.port, tail.port_R) annotation (Line(points={{-40,-40},{-20,-40},{-20,-4},{0,-4}}, color={0,128,255}));
  annotation (
    experiment(StopTime=3.0, Interval=0.001, Tolerance=1e-8),
    Documentation(info="<html>
<p>Ogon podłączony do dwóch zbiorników (idealne źródła ciśnienia), skok różnicy ciśnień o 30 kPa.
Ogon wychyla się z przeregulowaniem i oscylacjami, a potem ustala na kącie <code>&theta; = D_tail·&Delta;p/k</code>.</p>
<p>Oczekiwania: kąt końcowy zgodny ze wzorem (&lt; 1%), energia hydrauliczna dostarczona = energia kinetyczna
+ sprężysta + rozproszona (&lt; 1%).</p>
</html>"));
end TailStaticEnergy;
