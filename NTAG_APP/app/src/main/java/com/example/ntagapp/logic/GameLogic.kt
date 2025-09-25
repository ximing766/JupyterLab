package com.example.ntagapp.logic

import com.example.ntagapp.model.GameChoice
import com.example.ntagapp.model.GameResult
import kotlin.random.Random

/**
 * Simple game logic for Rock Paper Scissors
 */
class GameLogic {
    
    /**
     * Generate random device choice
     */
    fun generateDeviceChoice(): GameChoice {
        return GameChoice.values().random()
    }
    
    /**
     * Determine game result from user's perspective
     */
    fun determineResult(userChoice: GameChoice, deviceChoice: GameChoice): GameResult {
        return when {
            userChoice == deviceChoice -> GameResult.DRAW
            (userChoice == GameChoice.ROCK && deviceChoice == GameChoice.SCISSORS) ||
            (userChoice == GameChoice.PAPER && deviceChoice == GameChoice.ROCK) ||
            (userChoice == GameChoice.SCISSORS && deviceChoice == GameChoice.PAPER) -> GameResult.WIN
            else -> GameResult.LOSE
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
     * Get game statistics summary
     */
    fun getGameStatistics(results: List<GameResult>): Map<String, Any> {
        val totalGames = results.size
        val wins = results.count { it == GameResult.WIN }
        val losses = results.count { it == GameResult.LOSE }
        val draws = results.count { it == GameResult.DRAW }
        val winRate = if (totalGames > 0) wins.toFloat() / totalGames else 0f
        
        return mapOf(
            "totalGames" to totalGames,
            "wins" to wins,
            "losses" to losses,
            "draws" to draws,
            "winRate" to winRate
        )
    }
}