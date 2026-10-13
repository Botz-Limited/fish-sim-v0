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
    object      preciceFunctionObject;
}
// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //

// Loaded from controlDict (functions section). The adapter exchanges data with
// preCICE in every step: sends the forces on the tail, receives displacements.
preCICE_Adapter
{
    type            preciceAdapterFunctionObject;
    libs            (preciceAdapterFunctionObject);
    errors          strict;     // adapter error = stop the run
}

// ************************************************************************* //
