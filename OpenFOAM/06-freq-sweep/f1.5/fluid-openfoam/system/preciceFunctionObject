/*--------------------------------*- C++ -*----------------------------------*\
  =========                 |
  \\      /  F ield         | OpenFOAM: The Open Source CFD Toolbox
   \\    /   O peration     | Wersja: v2606 (openfoam.com)
    \\  /    A nd           |
     \\/     M anipulation  | Demo FSI ogona ryby
\*---------------------------------------------------------------------------*/
FoamFile
{
    version     2.0;
    format      ascii;
    class       dictionary;
    object      preciceFunctionObject;
}
// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //

// Ładowany z controlDict (sekcja functions). Adapter wymienia dane z preCICE
// w każdym kroku: wysyła siły na ogonie, odbiera przemieszczenia.
preCICE_Adapter
{
    type            preciceAdapterFunctionObject;
    libs            (preciceAdapterFunctionObject);
    errors          strict;     // błąd adaptera = zatrzymanie obliczeń
}

// ************************************************************************* //
