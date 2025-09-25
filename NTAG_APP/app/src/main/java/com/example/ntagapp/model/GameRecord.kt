package com.example.ntagapp.model

import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

/**
 * Data class representing a single game record
 */
data class GameRecord(
    val id: Long = 0,
    val userChoice: GameChoice,
    val deviceChoice: GameChoice,
    val result: GameResult,
    val timestamp: Long = System.currentTimeMillis()
) {
    /**
     * Get formatted timestamp string
     */
    fun getFormattedTime(): String {
        val formatter = SimpleDateFormat("MM-dd HH:mm", Locale.getDefault())
        return formatter.format(Date(timestamp))
    }
    
    /**
     * Get detailed formatted timestamp string
     */
    fun getDetailedFormattedTime(): String {
        val formatter = SimpleDateFormat("yyyy-MM-dd HH:mm:ss", Locale.getDefault())
        return formatter.format(Date(timestamp))
    }
    
    /**
     * Get game summary string
     */
    fun getGameSummary(): String {
        return "${userChoice.getDisplayName()} vs ${deviceChoice.getDisplayName()} - ${result.getDisplayName()}"
    }
}