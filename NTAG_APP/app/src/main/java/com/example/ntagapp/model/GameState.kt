package com.example.ntagapp.model

/**
 * Data class representing the current state of the game
 */
data class GameState(
    val userChoice: GameChoice? = null,
    val deviceChoice: GameChoice? = null,
    val result: GameResult? = null,
    val isLoading: Boolean = false,
    val isGameActive: Boolean = false,
    val score: Int = 0,
    val userScore: Int = 0,
    val deviceScore: Int = 0,
    val currentStreak: Int = 0,
    val showResult: Boolean = false,
    val animationState: AnimationState = AnimationState.IDLE
) {
    /**
     * Check if user has made a choice
     */
    val hasUserChoice: Boolean
        get() = userChoice != null
    
    /**
     * Check if game round is complete
     */
    val isRoundComplete: Boolean
        get() = userChoice != null && deviceChoice != null && result != null
    
    /**
     * Check if user can make a choice
     */
    val canMakeChoice: Boolean
        get() = !isLoading && !isGameActive && userChoice == null
}

/**
 * Enum representing different animation states
 */
enum class AnimationState {
    IDLE,
    USER_SELECTING,
    DEVICE_THINKING,
    SHOWING_RESULT,
    CELEBRATING,
    DISAPPOINTED,
    NEUTRAL
}