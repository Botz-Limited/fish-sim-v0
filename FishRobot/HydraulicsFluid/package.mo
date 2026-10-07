within FishRobot;
package HydraulicsFluid "Etap 9 (opcja): te same komponenty hydrauliki na złączach Modelica.Fluid (do porównania)"
  extends Modelica.Icons.VariantsPackage;

  annotation (Documentation(info="<html>
<p>Ten sam obwód co w <code>FishRobot.Hydraulics</code>, ale na złączach <code>Modelica.Fluid.Interfaces.FluidPort</code>
z pełnym modelem medium (<code>Modelica.Media.Water.ConstantPropertyLiquidWater</code>). Służy tylko do porównania
z własnym lekkim pakietem (scenariusz <code>Examples.HydraulicsMSLFluid</code>).</p>
<p><b>Czego w Modelica.Fluid nie ma</b> i trzeba było dopisać: pompy wyporowej (MSL ma tylko pompy wirowe
z charakterystyką wysokości podnoszenia), komory o podatnych ściankach (naczynia MSL mają stałą objętość albo
swobodne lustro cieczy) i zaworu przelewowego (złożony tu z zaworu liniowego i czujnika różnicy ciśnień).
Z biblioteki wprost pochodzą: rura (<code>Pipes.StaticPipe</code>), straty miejscowe
(<code>Fittings.SimpleGenericOrifice</code>), zawór (<code>Valves.ValveLinear</code>), czujnik
(<code>Sensors.RelativePressure</code>) i baza naczynia (<code>Vessels.BaseClasses.PartialLumpedVessel</code>).</p>
<p><b>Złącze Fluid</b> przenosi ciśnienie <code>p</code> (potencjał), <b>masowe</b> natężenie przepływu
<code>m_flow</code> (zmienna przepływowa) oraz zmienne strumieniowe (<code>stream</code>): entalpię właściwą
<code>h_outflow</code> i skład <code>Xi_outflow</code>. Dzięki nim biblioteka liczy bilans energii z temperaturą
cieczy, ale każdy komponent musi definiować, co wypływa z każdego portu (<code>inStream()</code>).</p>
</html>"));
end HydraulicsFluid;
