cmake_minimum_required(VERSION 3.24)
project(MyProjectConsumer LANGUAGES CXX)

find_package(MyProject CONFIG REQUIRED)

add_executable(myproject_consumer main.cpp)
target_link_libraries(myproject_consumer PRIVATE MyProject::cpp_wrapper)

