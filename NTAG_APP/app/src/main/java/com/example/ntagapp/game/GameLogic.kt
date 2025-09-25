package com.example.ntagapp.game

import com.example.ntagapp.model.GameChoice
import com.example.ntagapp.model.GameResult
import kotlin.random.Random

/**
 * Game logic manager for Rock Paper Scissors
 */
class GameLogic {
    
    /**
     * Generate device choice with optional strategy
     */
    fun generateDeviceChoice(
        userHistory: List<GameChoice> = emptyList(),
        difficulty: GameDifficulty = GameDifficulty.RANDOM
    ): GameChoice {
        return when (difficulty) {
            GameDifficulty.RANDOM -> generateRandomChoice()
            GameDifficulty.EASY -> generateEasyChoice(userHistory)
            GameDifficulty.MEDIUM -> generateMediumChoice(userHistory)
            GameDifficulty.HARD -> generateHardChoice(userHistory)
        }
    }
    
    /**
     * Determine game result from user's perspective
     */
    fun determineResult(userChoice: GameChoice, deviceChoice: GameChoice): GameResult {
        return when {
            userChoice == deviceChoice -> GameResult.DRAW
            isUserWin(userChoice, deviceChoice) -> GameResult.WIN
            else -> GameResult.LOSE
        }
    }
    
    /**
     * Check if user wins against device
     */
    private fun isUserWin(userChoice: GameChoice, deviceChoice: GameChoice): Boolean {
        return when (userChoice) {
            GameChoice.ROCK -> deviceChoice == GameChoice.SCISSORS
            GameChoice.PAPER -> deviceChoice == GameChoice.ROCK
            GameChoice.SCISSORS -> deviceChoice == GameChoice.PAPER
        }
    }
    
    /**
     * Generate completely random choice
     */
    private fun generateRandomChoice(): GameChoice {
        return GameChoice.values()[Random.nextInt(GameChoice.values().size)]
    }
    
    /**
     * Easy difficulty - slightly favors user winning
     */
    private fun generateEasyChoice(userHistory: List<GameChoice>): GameChoice {
        if (userHistory.isEmpty()) return generateRandomChoice()
        
        val lastChoice = userHistory.last()
        
        // 60% chance to choose what user beats, 40% random
        return if (Random.nextFloat() < 0.6f) {
            when (lastChoice) {
                GameChoice.ROCK -> GameChoice.SCISSORS // User wins with rock
                GameChoice.PAPER -> GameChoice.ROCK // User wins with paper
                GameChoice.SCISSORS -> GameChoice.PAPER // User wins with scissors
            }
        } else {
            generateRandomChoice()
        }
    }
    
    /**
     * Medium difficulty - analyzes recent patterns
     */
    private fun generateMediumChoice(userHistory: List<GameChoice>): GameChoice {
        if (userHistory.size < 3) return generateRandomChoice()
        
        val recentChoices = userHistory.takeLast(3)
        val mostFrequent = recentChoices.groupingBy { it }.eachCount().maxByOrNull { it.value }?.key
        
        return if (mostFrequent != null && Random.nextFloat() < 0.7f) {
            // Counter the most frequent choice
            when (mostFrequent) {
                GameChoice.ROCK -> GameChoice.PAPER
                GameChoice.PAPER -> GameChoice.SCISSORS
                GameChoice.SCISSORS -> GameChoice.ROCK
            }
        } else {
            generateRandomChoice()
        }
    }
    
    /**
     * Hard difficulty - advanced pattern recognition
     */
    private fun generateHardChoice(userHistory: List<GameChoice>): GameChoice {
        if (userHistory.size < 5) return generateMediumChoice(userHistory)
        
        val recentChoices = userHistory.takeLast(5)
        
        // Look for patterns
        val pattern = detectPattern(recentChoices)
        if (pattern != null) {
            return counterChoice(pattern)
        }
        
        // Analyze frequency and counter most common
        val choiceFrequency = userHistory.groupingBy { it }.eachCount()
        val mostCommon = choiceFrequency.maxByOrNull { it.value }?.key
        
        return if (mostCommon != null) {
            counterChoice(mostCommon)
        } else {
            generateRandomChoice()
        }
    }
    
    /**
     * Detect simple patterns in user choices
     */
    private fun detectPattern(choices: List<GameChoice>): GameChoice? {
        if (choices.size < 3) return null
        
        // Check for alternating pattern
        if (choices.size >= 4) {
            val isAlternating = choices.zipWithNext().all { (a, b) -> a != b }
            if (isAlternating) {
                // Predict next in alternating sequence
                val lastTwo = choices.takeLast(2)
                val remaining = GameChoice.values().toSet() - lastTwo.toSet()
                if (remaining.size == 1) {
                    return remaining.first()
                }
            }
        }
        
        // Check for repetition pattern
        val last = choices.last()
        val consecutiveCount = choices.takeLastWhile { it == last }.size
        if (consecutiveCount >= 2) {
            return last // Predict user will continue the pattern
        }
        
        return null
    }
    
    /**
     * Get the choice that beats the given choice
     */
    private fun counterChoice(choice: GameChoice): GameChoice {
        return when (choice) {
            GameChoice.ROCK -> GameChoice.PAPER
            GameChoice.PAPER -> GameChoice.SCISSORS
            GameChoice.SCISSORS -> GameChoice.ROCK
        }
    }
    
    /**
     * Calculate win rate from game history
     */
    fun calculateWinRate(results: List<GameResult>): Float {
        if (results.isEmpty()) return 0f
        val wins = results.count { it == GameResult.WIN }
        return wins.toFloat() / results.size
    }
    
    /**
     * Get game statistics
     */
    fun getGameStatistics(results: List<GameResult>): GameStatistics {
        val totalGames = results.size
        val wins = results.count { it == GameResult.WIN }
        val losses = results.count { it == GameResult.LOSE }
        val draws = results.count { it == GameResult.DRAW }
        
        return GameStatistics(
            totalGames = totalGames,
            wins = wins,
            losses = losses,
            draws = draws,
            winRate = if (totalGames > 0) wins.toFloat() / totalGames else 0f
        )
    }
}

/**
 * Game difficulty levels
 */
enum class GameDifficulty {
    RANDOM,  // Completely random choices
    EASY,    // Slightly favors user
    MEDIUM,  // Basic pattern recognition
    HARD     // Advanced AI with pattern analysis
}

/**
 * Game statistics data class
 */
data class GameStatistics(
    val totalGames: Int,
    val wins: Int,
    val losses: Int,
    val draws: Int,
    val winRate: Float
)

/**
 * Choice analysis for statistics
 */
data class ChoiceAnalysis(
    val choice: GameChoice,
    val count: Int,
    val winRate: Float
)

/**
 * Performance metrics
 */
data class PerformanceMetrics(
    val currentStreak: Int,
    val longestWinStreak: Int,
    val longestLoseStreak: Int,
    val averageGameDuration: Long // in milliseconds
)