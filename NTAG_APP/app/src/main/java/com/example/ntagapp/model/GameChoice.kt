package com.example.ntagapp.model

/**
 * Enum representing the three possible choices in Rock-Paper-Scissors game
 */
enum class GameChoice {
    ROCK,
    PAPER,
    SCISSORS;
    
    /**
     * Get display name for the choice
     */
    fun getDisplayName(): String {
        return when (this) {
            ROCK -> "石头"
            PAPER -> "布"
            SCISSORS -> "剪刀"
        }
    }
    
    /**
     * Get emoji representation for the choice
     */
    fun getEmoji(): String {
        return when (this) {
            ROCK -> "🪨"
            PAPER -> "📄"
            SCISSORS -> "✂️"
        }
    }
    
    /**
     * Determine if this choice beats the other choice
     */
    fun beats(other: GameChoice): Boolean {
        return when (this) {
            ROCK -> other == SCISSORS
            PAPER -> other == ROCK
            SCISSORS -> other == PAPER
        }
    }
}