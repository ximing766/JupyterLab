#include <jni.h>
#include <string>
#include <android/log.h>
#include "rssi_dir.h"

#define LOG_TAG "UWB_JNI"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)
#define LOGE(...) __android_log_print(ANDROID_LOG_ERROR, LOG_TAG, __VA_ARGS__)

extern "C" JNIEXPORT jfloat JNICALL
Java_com_example_uwbota_RssiDirNative_estimateAngle(
        JNIEnv* env,
        jobject /* this */,
        jfloat rssi_a,
        jfloat rssi_b,
        jfloat dist_cm) {
    
    LOGI("Calling de_estimate_angle with rssi_a=%f, rssi_b=%f, dist_cm=%f", rssi_a, rssi_b, dist_cm);
    float result = de_estimate_angle(rssi_a, rssi_b, dist_cm);
    LOGI("de_estimate_angle returned: %f", result);
    return result;
}

extern "C" JNIEXPORT jint JNICALL
Java_com_example_uwbota_RssiDirNative_selfTest(
        JNIEnv* env,
        jobject /* this */) {
    
    const int MAX_ITEMS = 20;
    float angles[MAX_ITEMS];
    float dists[MAX_ITEMS];
    
    LOGI("Calling de_selftest with max_items=%d", MAX_ITEMS);
    int count = de_selftest(angles, dists, MAX_ITEMS);
    LOGI("de_selftest returned count: %d", count);
    
    if (count > 0) {
        for (int i = 0; i < count && i < MAX_ITEMS; ++i) {
             LOGI("Selftest Item [%d]: Angle=%f, Dist=%f", i, angles[i], dists[i]);
        }
    } else {
        LOGE("de_selftest returned no items or error");
    }
    
    return count;
}
