within FishRobot.Tests;
model GearPumpCharacteristic "Test: charakterystyka pompy przy stałej prędkości i zmiennym ciśnieniu"
  extends Modelica.Icons.Example;

  Modelica.Mechanics.Rotational.Sources.ConstantSpeed drive(w_fixed=300, phi(start=0, fixed=true)) "Napęd o stałej prędkości"
    annotation (Placement(transformation(extent={{-40,40},{-20,60}})));
  FishRobot.Hydraulics.GearPump pump
    annotation (Placement(transformation(extent={{-10,-10},{10,10}})));
  FishRobot.Hydraulics.Reservoir inlet
    annotation (Placement(transformation(extent={{-60,-10},{-40,10}})));
  FishRobot.Hydraulics.Reservoir outlet(use_p_in=true)
    annotation (Placement(transformation(extent={{60,-10},{40,10}})));
  Modelica.Blocks.Sources.Ramp p_out(offset=1.01325e5 - 20e3, height=80e3, duration=1)
    "Ciśnienie na wylocie: od -20 kPa (tryb silnika) do +60 kPa (tryb pompy)"
    annotation (Placement(transformation(extent={{100,-10},{80,10}})));
equation
  connect(drive.flange, pump.flange) annotation (Line(points={{-20,50},{0,50},{0,10}}));
  connect(inlet.port, pump.port_a) annotation (Line(points={{-40,0},{-10,0}}, color={0,128,255}));
  connect(pump.port_b, outlet.port) annotation (Line(points={{10,0},{40,0}}, color={0,128,255}));
  connect(p_out.y, outlet.p_in) annotation (Line(points={{79,0},{64,0}}, color={0,0,127}));
  annotation (
    experiment(StopTime=1.0, Interval=0.002, Tolerance=1e-8),
    Documentation(info="<html>
<p>Pompa kręcona ze stałą prędkością 300 rad/s, ciśnienie na wylocie rośnie od -20 kPa do +60 kPa
względem wlotu. Dla &Delta;p &lt; 0 ciśnienie „pomaga” pompie (ciecz oddaje energię, tryb silnika
hydraulicznego), dla &Delta;p &gt; 0 pompa pracuje normalnie.</p>
<p>Oczekiwania: <code>V_flow = D·&omega; - k_leak·&Delta;p</code>, w trybie pompy
<code>&tau; = D·&Delta;p/&eta;_m</code>, straty tarcia nigdy ujemne, bilans mocy pompy zamknięty.</p>
</html>"));
end GearPumpCharacteristic;
