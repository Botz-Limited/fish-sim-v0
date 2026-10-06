within FishRobot.Tests;
model BallastStatics "Test: pływalność neutralna, dodatnia i ujemna; niestabilność przy ściśliwym kadłubie"
  extends Modelica.Icons.Example;
  parameter Modelica.Units.SI.Volume V_n = 6e-6 "Objętość neutralna (jak w VerticalDynamics)";
  parameter Modelica.Units.SI.Volume dV = 1e-6 "Odchyłka objętości pęcherza";
  parameter Modelica.Units.SI.Position z0 = -3.0 "Głębokość startowa (dość głęboko, żeby lżejsza ryba nie wypłynęła w 60 s)";
  parameter Modelica.Units.SI.Position dz = -0.01 "Małe zaburzenie położenia startowego (1 cm w dół)";

  // Objętość neutralna na głębokości z0 przy ściśliwym powietrzu: trzeba dołożyć tyle, ile ścisnęło się powietrze.
  parameter Modelica.Units.SI.Volume V_n_comp = V_n + fishComp.V_air0
    - fishComp.V_air0*fishComp.p_atm/(fishComp.p_atm + fishComp.rho*Modelica.Constants.g_n*(-z0))
    "Objętość neutralna na głębokości z0 dla kadłuba ze ściśliwym powietrzem";

  FishRobot.Buoyancy.VerticalDynamics fishNeutral(z_start=z0) "V_b = neutralna"
    annotation (Placement(transformation(extent={{0,60},{20,80}})));
  FishRobot.Buoyancy.VerticalDynamics fishLight(z_start=z0) "V_b = neutralna + 1 ml"
    annotation (Placement(transformation(extent={{0,20},{20,40}})));
  FishRobot.Buoyancy.VerticalDynamics fishHeavy(z_start=z0) "V_b = neutralna - 1 ml"
    annotation (Placement(transformation(extent={{0,-20},{20,0}})));
  FishRobot.Buoyancy.VerticalDynamics fishRigid(z_start=z0 + dz) "Kadłub sztywny, zaburzenie 1 cm"
    annotation (Placement(transformation(extent={{0,-60},{20,-40}})));
  FishRobot.Buoyancy.VerticalDynamics fishComp(z_start=z0 + dz, useCompressibility=true)
    "Kadłub ze ściśliwym powietrzem, zaburzenie 1 cm"
    annotation (Placement(transformation(extent={{0,-100},{20,-80}})));
  Modelica.Blocks.Sources.Constant vNeutral(k=V_n) annotation (Placement(transformation(extent={{-60,60},{-40,80}})));
  Modelica.Blocks.Sources.Constant vLight(k=V_n + dV) annotation (Placement(transformation(extent={{-60,20},{-40,40}})));
  Modelica.Blocks.Sources.Constant vHeavy(k=V_n - dV) annotation (Placement(transformation(extent={{-60,-20},{-40,0}})));
  Modelica.Blocks.Sources.Constant vComp(k=V_n_comp) annotation (Placement(transformation(extent={{-60,-100},{-40,-80}})));
equation
  connect(vNeutral.y, fishNeutral.V_b) annotation (Line(points={{-39,70},{-2,70}}, color={0,0,127}));
  connect(vLight.y, fishLight.V_b) annotation (Line(points={{-39,30},{-2,30}}, color={0,0,127}));
  connect(vHeavy.y, fishHeavy.V_b) annotation (Line(points={{-39,-10},{-2,-10}}, color={0,0,127}));
  connect(vNeutral.y, fishRigid.V_b) annotation (Line(points={{-39,70},{-20,70},{-20,-50},{-2,-50}}, color={0,0,127}));
  connect(vComp.y, fishComp.V_b) annotation (Line(points={{-39,-90},{-2,-90}}, color={0,0,127}));
  annotation (
    experiment(StopTime=60, Interval=0.05, Tolerance=1e-8),
    Documentation(info="<html>
<p>Pięć niezależnych ryb bez regulatora, ze stałą objętością pęcherza:</p>
<ul>
<li><code>fishNeutral</code> – pęcherz neutralny: ryba stoi w miejscu (<code>z' &rarr; 0</code>),</li>
<li><code>fishLight</code> / <code>fishHeavy</code> – ±1 ml: wynurza się / tonie ze stałą prędkością graniczną
(wypór równoważy opór),</li>
<li><code>fishRigid</code> – sztywny kadłub, start 1 cm poniżej: neutralność nie zależy od głębokości, więc ryba zostaje
tam, gdzie ją postawiono (<b>równowaga obojętna</b>),</li>
<li><code>fishComp</code> – kadłub z kieszenią powietrza, neutralny dokładnie na -3 m, start 1 cm niżej: powietrze jest
tam bardziej ściśnięte, ryba jest odrobinę cięższa i tonie coraz szybciej (<b>równowaga niestabilna</b>).</li>
</ul>
</html>"));
end BallastStatics;
