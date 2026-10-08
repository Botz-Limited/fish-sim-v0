cmake_minimum_required(VERSION 3.16)
project(fish_stonefish_demo CXX)

# Stonefish 1.5 wymaga C++20 (tak jest skompilowana biblioteka).
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
if(NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE Release)
endif()
add_compile_options(-Wall -Wextra)

# Biblioteka Stonefish (zainstalowana przez "make install"; jeśli w nietypowym
# miejscu, podaj -DCMAKE_PREFIX_PATH=<prefiks>). Pakiet sam szuka OpenGL, SDL2, Freetype, OpenMP.
find_package(Stonefish REQUIRED)
# Pakiet akceptuje tylko dokładną wersję, więc sprawdzamy sami: demo pisane i testowane z 1.5.0.
if(NOT Stonefish_VERSION VERSION_EQUAL 1.5.0)
    message(WARNING "Znaleziono Stonefish ${Stonefish_VERSION}, demo było sprawdzane z 1.5.0 – składnia XML i API mogą się różnić.")
endif()
# Nagłówki Stonefish dołączają GLM (tylko nagłówki), a pakiet go nie eksportuje.
find_package(glm REQUIRED)

# Jedna biblioteka z logiką demo – wspólna dla aplikacji graficznej, konsolowej i testów.
add_library(fishcore STATIC
    src/Config.cpp
    src/Hydraulics.cpp
    src/TailDriver.cpp
    src/Controllers.cpp
    src/FinLift.cpp
    src/FishSimManager.cpp
)
target_include_directories(fishcore PUBLIC src third_party)
# Nagłówki Stonefish mają #include <SDL2/...> – potrzebny katalog NAD include/SDL2.
foreach(dir ${SDL2_INCLUDE_DIRS})
    get_filename_component(parent "${dir}" DIRECTORY)
    target_include_directories(fishcore PUBLIC "${dir}" "${parent}")
endforeach()
target_link_libraries(fishcore PUBLIC Stonefish::Stonefish glm::glm)
# Katalog projektu (config/, data/, results/) – można nadpisać zmienną środowiskową FISH_ROOT.
target_compile_definitions(fishcore PUBLIC FISH_ROOT_DIR="${CMAKE_CURRENT_SOURCE_DIR}")

add_executable(fish_gui src/main_gui.cpp)
target_link_libraries(fish_gui PRIVATE fishcore)

add_executable(fish_console src/main_console.cpp)
target_link_libraries(fish_console PRIVATE fishcore)

# Testy jednostkowe (bez symulatora): hydraulika, TailDriver, regulatory.
add_executable(unit_tests tests/unit_tests.cpp)
target_link_libraries(unit_tests PRIVATE fishcore)

enable_testing()
add_test(NAME unit_tests COMMAND unit_tests)
add_test(NAME scenario_tests COMMAND ${CMAKE_CURRENT_SOURCE_DIR}/tests/run_tests.sh ${CMAKE_CURRENT_BINARY_DIR})
