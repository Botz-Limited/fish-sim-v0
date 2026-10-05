# SofaCHOLMOD – kopia źródeł w repo

Wtyczka SOFA z solverem `EigenCholmodSupernodalLLT` (CHOLMOD/SuiteSparse), skopiowana tu, żeby
instalacja nie zależała od gałęzi master SOFA (master bywa przepisywany).

- Źródło: https://github.com/sofa-framework/sofa, commit `6c3e21f204ab78cdaedd94d8cf412e4f2e002f1e`
  (master, 5.10.2026), katalog `applications/plugins/SofaCHOLMOD`.
- Licencja: LGPL 2.1+ (`LICENSE-LGPL.md`, jak cała SOFA). Autorzy: zespół SOFA (`Authors.txt` w repo SOFA).
- Bez zmian w plikach wtyczki. Dodatki do budowy na binarce SOFA v26.06 (`scripts/build_cholmod_plugin.sh`):
  - `overlay/.../EigenSolverFactory.h` – ten nagłówek z tego samego commita SOFA. Wtyczka używa
    szablonu `registerProxyType`, dodanego po v26.06; to czysty dodatek w nagłówku, bez zmiany
    układu klasy, więc podanie go przed nagłówkami binarki (`-I`) wystarcza.
  - `cmake/FindCHOLMOD.cmake` – `cmake/Modules/FindCHOLMOD.cmake` z tego commita bez próby
    użycia configu CMake z SuiteSparse (config z Fedory odwołuje się do nieistniejących
    plików `*_static.cmake`); zostaje ręczne wyszukanie nagłówka i bibliotek.
