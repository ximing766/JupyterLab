package com.example.ntagapp.model

/**
 * Enum representing the possible game results from user's perspective
 */
enum class GameResult {
    WIN,
    LOSE,
    DRAW;
    
    /**
     * Get display name for the result
     */
    fun getDisplayName(): String {
        return when (this) {
            WIN -> "胜利"
            LOSE -> "失败"
            DRAW -> "平局"
        }
    }
    
    /**
     * Get emoji representation for the result
     */
    fun getEmoji(): String {
        return when (this) {
            WIN -> "🎉"
            LOSE -> "😢"
            DRAW -> "🤝"
        }
    }
    
    /**
     * Get color representation for the result (Material3 color scheme)
     */
    fun getColorName(): String {
        return when (this) {
            WIN -> "success"
            LOSE -> "error"
            DRAW -> "warning"
        }
    }
}