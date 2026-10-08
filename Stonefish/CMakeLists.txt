cmake_minimum_required(VERSION 3.16)
project(fish_stonefish_demo CXX)

# Stonefish 1.5 requires C++20 (that is how the library is compiled).
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
if(NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE Release)
endif()
add_compile_options(-Wall -Wextra)

# Stonefish library (installed with "make install"; if in an unusual
# location, pass -DCMAKE_PREFIX_PATH=<prefix>). The package itself finds OpenGL, SDL2, Freetype, OpenMP.
find_package(Stonefish REQUIRED)
# The package accepts only an exact version, so we check ourselves: the demo was written and tested with 1.5.0.
if(NOT Stonefish_VERSION VERSION_EQUAL 1.5.0)
    message(WARNING "Found Stonefish ${Stonefish_VERSION}, the demo was tested with 1.5.0 – XML syntax and API may differ.")
endif()
# Stonefish headers include GLM (header-only), but the package does not export it.
find_package(glm REQUIRED)

# A single library with the demo logic – shared by the graphical app, the console app and the tests.
add_library(fishcore STATIC
    src/Config.cpp
    src/Hydraulics.cpp
    src/TailDriver.cpp
    src/Controllers.cpp
    src/FinLift.cpp
    src/FishSimManager.cpp
)
target_include_directories(fishcore PUBLIC src third_party)
# Stonefish headers have #include <SDL2/...> – the directory ABOVE include/SDL2 is needed.
foreach(dir ${SDL2_INCLUDE_DIRS})
    get_filename_component(parent "${dir}" DIRECTORY)
    target_include_directories(fishcore PUBLIC "${dir}" "${parent}")
endforeach()
target_link_libraries(fishcore PUBLIC Stonefish::Stonefish glm::glm)
# Project directory (config/, data/, results/) – can be overridden with the FISH_ROOT environment variable.
target_compile_definitions(fishcore PUBLIC FISH_ROOT_DIR="${CMAKE_CURRENT_SOURCE_DIR}")

add_executable(fish_gui src/main_gui.cpp)
target_link_libraries(fish_gui PRIVATE fishcore)

add_executable(fish_console src/main_console.cpp)
target_link_libraries(fish_console PRIVATE fishcore)

# Unit tests (without the simulator): hydraulics, TailDriver, controllers.
add_executable(unit_tests tests/unit_tests.cpp)
target_link_libraries(unit_tests PRIVATE fishcore)

enable_testing()
add_test(NAME unit_tests COMMAND unit_tests)
add_test(NAME scenario_tests COMMAND ${CMAKE_CURRENT_SOURCE_DIR}/tests/run_tests.sh ${CMAKE_CURRENT_BINARY_DIR})
