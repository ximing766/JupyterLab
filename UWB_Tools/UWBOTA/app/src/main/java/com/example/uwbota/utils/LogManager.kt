package com.example.uwbota.utils

import android.util.Log

/**
 * 统一日志管理类
 * 只保留两个接口：控制台输出和界面日志区域输出
 */
object LogManager {
    private const val TAG = "UWB_OTA"
    
    // 界面日志回调
    private var uiLogCallback: ((String) -> Unit)? = null
    
    /**
     * 设置界面日志回调
     */
    fun setUiLogCallback(callback: (String) -> Unit) {
        uiLogCallback = callback
    }
    
    /**
     * 清除界面日志回调
     */
    fun clearUiLogCallback() {
        uiLogCallback = null
    }
    
    /**
     * 输出信息日志
     * 同时输出到控制台和界面
     */
    fun i(message: String) {
        // 输出到控制台
        Log.i(TAG, message)
        // 输出到界面
        uiLogCallback?.invoke(message)
    }
    
    /**
     * 输出调试日志
     * 同时输出到控制台和界面
     */
    fun d(message: String) {
        // 输出到控制台
        Log.d(TAG, message)
        // 输出到界面
        uiLogCallback?.invoke(message)
    }
    
    /**
     * 输出警告日志
     * 同时输出到控制台和界面
     */
    fun w(message: String) {
        // 输出到控制台
        Log.w(TAG, message)
        // 输出到界面
        uiLogCallback?.invoke("警告: $message")
    }
    
    /**
     * 输出错误日志
     * 同时输出到控制台和界面
     */
    fun e(message: String) {
        // 输出到控制台
        Log.e(TAG, message)
        // 输出到界面
        uiLogCallback?.invoke("错误: $message")
    }
    
    /**
     * 只输出到控制台（不显示在界面）
     */
    fun consoleOnly(level: String, message: String) {
        when (level.lowercase()) {
            "i" -> Log.i(TAG, message)
            "d" -> Log.d(TAG, message)
            "w" -> Log.w(TAG, message)
            "e" -> Log.e(TAG, message)
            else -> Log.i(TAG, message)
        }
    }
    
    /**
     * 只输出到界面（不输出到控制台）
     */
    fun uiOnly(message: String) {
        uiLogCallback?.invoke(message)
    }
}