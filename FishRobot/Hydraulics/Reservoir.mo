within FishRobot.Hydraulics;
model Reservoir "Zbiornik o zadanym ciśnieniu (stałym lub z wejścia)"
  parameter Boolean use_p_in = false "= true: ciśnienie z wejścia p_in"
    annotation (Evaluate=true, choices(checkBox=true));
  parameter Modelica.Units.SI.AbsolutePressure p = 1.01325e5 "Ciśnienie zbiornika (gdy use_p_in = false)"
    annotation (Dialog(enable=not use_p_in));
  FishRobot.Interfaces.HydraulicPort_a port
    annotation (Placement(transformation(extent={{90,-10},{110,10}})));
  Modelica.Blocks.Interfaces.RealInput p_in(unit="Pa") if use_p_in "Zadane ciśnienie"
    annotation (Placement(transformation(extent={{-140,-20},{-100,20}})));
protected
  Modelica.Blocks.Interfaces.RealInput p_internal(unit="Pa") "Ciśnienie wewnętrzne (pomocnicze)";
equation
  connect(p_in, p_internal);
  if not use_p_in then
    p_internal = p;
  end if;
  port.p = p_internal;
  annotation (
    Icon(graphics={
      Rectangle(extent={{-80,60},{80,-80}}, lineColor={0,0,0}, fillColor={255,255,255},
        fillPattern=FillPattern.Solid),
      Rectangle(extent={{-80,20},{80,-80}}, lineColor={0,128,255}, fillColor={0,128,255},
        fillPattern=FillPattern.Solid),
      Line(points={{80,0},{90,0}}, color={0,128,255}),
      Text(extent={{-150,110},{150,70}}, textString="%name", textColor={0,0,255})}),
    Documentation(info="<html>
<p>Idealne źródło ciśnienia: <code>port.p = p</code> niezależnie od przepływu (bardzo duży zbiornik
lub otwarta woda wokół ryby). Przepływ wynika z reszty obwodu.</p>
<p>Wejście <code>p_in</code> pojawia się tylko przy <code>use_p_in = true</code> (złącze warunkowe, wzorzec z MSL).</p>
</html>"));
end Reservoir;
