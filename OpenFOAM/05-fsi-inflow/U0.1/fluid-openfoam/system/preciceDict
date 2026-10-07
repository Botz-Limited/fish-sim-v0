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
    object      preciceDict;
}
// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //

#include "caseParams"

// Konfiguracja adaptera OpenFOAM-preCICE
preciceConfig   "../precice-config.xml";

// Nazwa uczestnika – musi być zgodna z <participant name="Fluid"> w XML
participant     Fluid;

// Moduł FSI: siły na ścianach i ruch siatki
modules         (FSI);

interfaces
{
    Interface1
    {
        // siatka interfejsu po stronie płynu (nazwa z precice-config.xml)
        mesh        Fluid-Mesh;
        // tylko ogon jest sprężysty; głowa jest sztywna i nie uczestniczy
        patches     (tail);
        // siły liczymy w środkach ścian, przemieszczenia też tam odbieramy
        // i adapter interpoluje je do punktów siatki
        locations   faceCenters;

        readData    (Displacement);
        writeData   (Force);
    }
}

FSI
{
    // Solver nieściśliwy liczy p/rho – adapter mnoży przez rho, żeby
    // wysłać siły w niutonach (na DEPTH = 1 m rozpiętości)
    rho         rho [1 -3 0 0 0 0 0] $RHO;
}

// ************************************************************************* //
