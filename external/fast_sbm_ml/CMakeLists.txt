cmake_minimum_required(VERSION 3.10)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

find_package(Torch REQUIRED)

add_library(c_fast_sbm_ml STATIC src/cpp/c_fast_sbm_ml.cpp src/cpp/c_fast_sbm_ml.h)
target_include_directories(c_fast_sbm_ml PUBLIC "${TORCH_INCLUDE_DIRS}")
target_link_libraries(c_fast_sbm_ml "${TORCH_LIBRARIES}")

add_executable(driver
    $<TARGET_OBJECTS:c_fast_sbm_ml>
    src/cpp/c_test_driver.cpp
)
target_link_libraries(driver "${TORCH_LIBRARIES}")