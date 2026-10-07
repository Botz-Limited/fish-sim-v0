# SofaCHOLMOD – vendored source copy

SOFA plugin with the `EigenCholmodSupernodalLLT` solver (CHOLMOD/SuiteSparse), copied here so that
the installation does not depend on the SOFA master branch (master gets rewritten).

- Source: https://github.com/sofa-framework/sofa, commit `6c3e21f204ab78cdaedd94d8cf412e4f2e002f1e`
  (master, 5.10.2026), directory `applications/plugins/SofaCHOLMOD`.
- License: LGPL 2.1+ (`LICENSE-LGPL.md`, like all of SOFA). Authors: the SOFA team (`Authors.txt` in the SOFA repo).
- No changes to the plugin files. Additions for building against the SOFA v26.06 binary (`scripts/build_cholmod_plugin.sh`):
  - `overlay/.../EigenSolverFactory.h` – this header from the same SOFA commit. The plugin uses
    the `registerProxyType` template, added after v26.06; it is a pure header addition, with no change
    to the class layout, so putting it before the binary's headers (`-I`) is sufficient.
  - `cmake/FindCHOLMOD.cmake` – `cmake/Modules/FindCHOLMOD.cmake` from this commit without the attempt
    to use the SuiteSparse CMake config (the Fedora config refers to nonexistent
    `*_static.cmake` files); what remains is a manual search for the header and libraries.
