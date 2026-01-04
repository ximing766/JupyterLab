package com.example.uwbota

object RssiDirNative {
    init {
        try {
            System.loadLibrary("uwbota_jni")
        } catch (e: UnsatisfiedLinkError) {
            e.printStackTrace()
        }
    }

    /**
     * Estimate angle based on RSSI values and distance.
     *
     * @param rssiA RSSI of antenna A
     * @param rssiB RSSI of antenna B
     * @param distCm Distance in centimeters
     * @return Estimated angle in degrees
     */
    external fun estimateAngle(rssiA: Float, rssiB: Float, distCm: Float): Float

    /**
     * Run internal self-test.
     * Results are printed to native log (logcat).
     *
     * @return Number of test items processed
     */
    external fun selfTest(): Int
}
