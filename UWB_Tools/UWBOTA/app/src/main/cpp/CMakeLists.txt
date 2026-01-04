cmake_minimum_required(VERSION 3.22.1)

project("uwbota")

# Import the prebuilt library
add_library(rssi_dir SHARED IMPORTED)
set_target_properties(rssi_dir PROPERTIES IMPORTED_LOCATION
    ${CMAKE_SOURCE_DIR}/../jniLibs/${ANDROID_ABI}/librssi_dir.so)

# Include directories
include_directories(${CMAKE_SOURCE_DIR}/include)

# Create the JNI wrapper library
add_library(uwbota_jni SHARED native-lib.cpp)

# Link libraries
find_library(log-lib log)

target_link_libraries(uwbota_jni
    rssi_dir
    ${log-lib})
