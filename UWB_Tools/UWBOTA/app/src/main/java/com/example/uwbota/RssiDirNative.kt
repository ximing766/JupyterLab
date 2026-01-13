package com.example.uwbota

object RssiDirNative {
    init {
        try {
            System.loadLibrary("uwbota_jni")
        } catch (e: UnsatisfiedLinkError) {
            e.printStackTrace()
        }
    }
    external fun estimateAngle(rssiA: Float, rssiB: Float, distCm: Float): Float
    external fun selfTest(): Int
}
