within ;
package FishRobot "Edukacyjny model systemowy robota-ryby: elektryka + hydraulika + mechanika + balast"
  extends Modelica.Icons.Package;

  annotation (
    uses(Modelica(version="4.1.0")),
    version="0.1.0",
    Documentation(info="<html>
<p>Uproszczony, <b>nieskalibrowany</b> model systemowy robota-ryby o skupionych parametrach (1D).
Wszystkie parametry geometryczne i konstrukcyjne to <b>PLACEHOLDERY – do identyfikacji</b>.</p>
<p>Hydraulika to własny lekki pakiet: złącze <code>HydraulicPort</code> ma ciśnienie <code>p</code>
(zmienna potencjałowa) i przepływ objętościowy <code>V_flow</code> (zmienna przepływowa, <code>flow</code>).
Iloczyn <code>p·V_flow</code> to moc hydrauliczna, więc bilans energii wynika bezpośrednio z połączeń.</p>
<p>Konwencja znaków: <code>V_flow &gt; 0</code> oznacza przepływ <b>do</b> komponentu przez dany port.</p>
</html>"));
end FishRobot;
