package com.example.ntagapp.model

/**
 * Data class representing game statistics
 */
data class GameStatistics(
    val totalGames: Int = 0,
    val wins: Int = 0,
    val losses: Int = 0,
    val draws: Int = 0,
    val maxWinStreak: Int = 0,
    val currentWinStreak: Int = 0,
    val maxLoseStreak: Int = 0,
    val currentLoseStreak: Int = 0
) {
    /**
     * Calculate win rate as percentage
     */
    val winRate: Float
        get() = if (totalGames > 0) (wins.toFloat() / totalGames.toFloat()) * 100f else 0f
    
    /**
     * Calculate lose rate as percentage
     */
    val loseRate: Float
        get() = if (totalGames > 0) (losses.toFloat() / totalGames.toFloat()) * 100f else 0f
    
    /**
     * Calculate draw rate as percentage
     */
    val drawRate: Float
        get() = if (totalGames > 0) (draws.toFloat() / totalGames.toFloat()) * 100f else 0f
    
    /**
     * Get formatted win rate string
     */
    fun getFormattedWinRate(): String {
        return String.format("%.1f%%", winRate)
    }
    
    /**
     * Get formatted lose rate string
     */
    fun getFormattedLoseRate(): String {
        return String.format("%.1f%%", loseRate)
    }
    
    /**
     * Get formatted draw rate string
     */
    fun getFormattedDrawRate(): String {
        return String.format("%.1f%%", drawRate)
    }
    
    /**
     * Check if player is on a winning streak
     */
    val isOnWinStreak: Boolean
        get() = currentWinStreak > 0
    
    /**
     * Check if player is on a losing streak
     */
    val isOnLoseStreak: Boolean
        get() = currentLoseStreak > 0
}