/*--------------------------------*- C++ -*----------------------------------*\
  =========                 |
  \\      /  F ield         | OpenFOAM: The Open Source CFD Toolbox
   \\    /   O peration     | Version: v2606 (openfoam.com)
    \\  /    A nd           |
     \\/     M anipulation  | Fish tail FSI demo
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

// OpenFOAM-preCICE adapter configuration
preciceConfig   "../precice-config.xml";

// Participant name – must match <participant name="Fluid"> in the XML
participant     Fluid;

// FSI module: wall forces and mesh motion
modules         (FSI);

interfaces
{
    Interface1
    {
        // interface mesh on the fluid side (name from precice-config.xml)
        mesh        Fluid-Mesh;
        // only the tail is elastic; the head is rigid and does not take part
        patches     (tail);
        // forces are computed at face centres, displacements are received there
        // too and the adapter interpolates them to the mesh points
        locations   faceCenters;

        readData    (Displacement);
        writeData   (Force);
    }
}

FSI
{
    // The incompressible solver computes p/rho – the adapter multiplies by rho
    // to send forces in newtons (per DEPTH = 1 m of span)
    rho         rho [1 -3 0 0 0 0 0] $RHO;
}

// ************************************************************************* //
