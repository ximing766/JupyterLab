package com.example.ntagapp.repository

import com.example.ntagapp.data.dao.GameRecordDao
import com.example.ntagapp.data.entity.GameRecordEntity
import com.example.ntagapp.model.GameChoice
import com.example.ntagapp.model.GameRecord
import com.example.ntagapp.model.GameResult
import com.example.ntagapp.model.GameStatistics
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.map
import kotlin.random.Random

/**
 * Repository for handling game-related data operations
 */
class GameRepository(private val gameRecordDao: GameRecordDao) {
    
    /**
     * Save a game record to the database
     */
    suspend fun saveGameRecord(gameRecord: GameRecord): Long {
        val entity = GameRecordEntity.fromDomainModel(gameRecord)
        return gameRecordDao.insertGameRecord(entity)
    }
    
    /**
     * Get all game records as Flow
     */
    fun getAllGameRecords(): Flow<List<GameRecord>> {
        return gameRecordDao.getAllGameRecords().map { entities ->
            entities.map { it.toDomainModel() }
        }
    }
    
    /**
     * Get recent game records with limit
     */
    fun getRecentGameRecords(limit: Int = 20): Flow<List<GameRecord>> {
        return gameRecordDao.getRecentGameRecords(limit).map { entities ->
            entities.map { it.toDomainModel() }
        }
    }
    
    /**
     * Get game statistics
     */
    suspend fun getGameStatistics(): GameStatistics {
        val totalGames = gameRecordDao.getTotalGamesCount()
        val wins = gameRecordDao.getWinsCount()
        val losses = gameRecordDao.getLossesCount()
        val draws = gameRecordDao.getDrawsCount()
        
        // Calculate streaks from recent games
        val recentGamesFlow = gameRecordDao.getRecentGameRecords(100)
        val recentGames = recentGamesFlow.map { entities -> entities.map { it.toDomainModel() } }
        val streaks = calculateStreaks(recentGames.first())
        
        return GameStatistics(
            totalGames = totalGames,
            wins = wins,
            losses = losses,
            draws = draws,
            maxWinStreak = streaks.maxWinStreak,
            currentWinStreak = streaks.currentWinStreak,
            maxLoseStreak = streaks.maxLoseStreak,
            currentLoseStreak = streaks.currentLoseStreak
        )
    }
    
    /**
     * Generate random device choice
     */
    fun generateDeviceChoice(): GameChoice {
        val choices = GameChoice.values()
        return choices[Random.nextInt(choices.size)]
    }
    
    /**
     * Determine game result based on user and device choices
     */
    fun determineGameResult(userChoice: GameChoice, deviceChoice: GameChoice): GameResult {
        return when {
            userChoice == deviceChoice -> GameResult.DRAW
            userChoice.beats(deviceChoice) -> GameResult.WIN
            else -> GameResult.LOSE
        }
    }
    
    /**
     * Play a complete game round
     */
    suspend fun playGameRound(userChoice: GameChoice): GameRecord {
        val deviceChoice = generateDeviceChoice()
        val result = determineGameResult(userChoice, deviceChoice)
        
        val gameRecord = GameRecord(
            userChoice = userChoice,
            deviceChoice = deviceChoice,
            result = result
        )
        
        val id = saveGameRecord(gameRecord)
        return gameRecord.copy(id = id)
    }
    
    /**
     * Delete all game records
     */
    suspend fun clearAllGameRecords() {
        gameRecordDao.deleteAllGameRecords()
    }
    
    /**
     * Delete old game records, keeping only recent ones
     */
    suspend fun cleanupOldRecords(keepCount: Int = 1000) {
        gameRecordDao.deleteOldGameRecords(keepCount)
    }
    
    /**
     * Calculate win/lose streaks from game records
     */
    private fun calculateStreaks(gameRecords: List<GameRecord>): StreakData {
        if (gameRecords.isEmpty()) {
            return StreakData()
        }
        
        var maxWinStreak = 0
        var currentWinStreak = 0
        var maxLoseStreak = 0
        var currentLoseStreak = 0
        
        var tempWinStreak = 0
        var tempLoseStreak = 0
        
        // Process games from most recent to oldest
        gameRecords.forEach { record ->
            when (record.result) {
                GameResult.WIN -> {
                    tempWinStreak++
                    tempLoseStreak = 0
                    maxWinStreak = maxOf(maxWinStreak, tempWinStreak)
                }
                GameResult.LOSE -> {
                    tempLoseStreak++
                    tempWinStreak = 0
                    maxLoseStreak = maxOf(maxLoseStreak, tempLoseStreak)
                }
                GameResult.DRAW -> {
                    tempWinStreak = 0
                    tempLoseStreak = 0
                }
            }
        }
        
        // Current streaks are the streaks at the beginning (most recent games)
        if (gameRecords.isNotEmpty()) {
            when (gameRecords.first().result) {
                GameResult.WIN -> currentWinStreak = tempWinStreak
                GameResult.LOSE -> currentLoseStreak = tempLoseStreak
                GameResult.DRAW -> {
                    currentWinStreak = 0
                    currentLoseStreak = 0
                }
            }
        }
        
        return StreakData(
            maxWinStreak = maxWinStreak,
            currentWinStreak = currentWinStreak,
            maxLoseStreak = maxLoseStreak,
            currentLoseStreak = currentLoseStreak
        )
    }
    
    /**
     * Data class for streak calculations
     */
    private data class StreakData(
        val maxWinStreak: Int = 0,
        val currentWinStreak: Int = 0,
        val maxLoseStreak: Int = 0,
        val currentLoseStreak: Int = 0
    )
}