cmake_minimum_required(VERSION 3.10)
project(cm C)
add_executable(cmake_main cmake_main.c)
install(TARGETS cmake_main DESTINATION bin)
