package com.example.ntagapp.data.dao

import androidx.room.Dao
import androidx.room.Delete
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import com.example.ntagapp.data.entity.GameRecordEntity
import kotlinx.coroutines.flow.Flow

/**
 * Data Access Object for game records
 */
@Dao
interface GameRecordDao {
    
    /**
     * Insert a new game record
     */
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertGameRecord(gameRecord: GameRecordEntity): Long
    
    /**
     * Get all game records ordered by timestamp descending
     */
    @Query("SELECT * FROM game_records ORDER BY timestamp DESC")
    fun getAllGameRecords(): Flow<List<GameRecordEntity>>
    
    /**
     * Get recent game records with limit
     */
    @Query("SELECT * FROM game_records ORDER BY timestamp DESC LIMIT :limit")
    fun getRecentGameRecords(limit: Int): Flow<List<GameRecordEntity>>
    
    /**
     * Get total number of games
     */
    @Query("SELECT COUNT(*) FROM game_records")
    suspend fun getTotalGamesCount(): Int
    
    /**
     * Get number of wins
     */
    @Query("SELECT COUNT(*) FROM game_records WHERE result = 'WIN'")
    suspend fun getWinsCount(): Int
    
    /**
     * Get number of losses
     */
    @Query("SELECT COUNT(*) FROM game_records WHERE result = 'LOSE'")
    suspend fun getLossesCount(): Int
    
    /**
     * Get number of draws
     */
    @Query("SELECT COUNT(*) FROM game_records WHERE result = 'DRAW'")
    suspend fun getDrawsCount(): Int
    
    /**
     * Get game records by result type
     */
    @Query("SELECT * FROM game_records WHERE result = :result ORDER BY timestamp DESC")
    fun getGameRecordsByResult(result: String): Flow<List<GameRecordEntity>>
    
    /**
     * Get game records within date range
     */
    @Query("SELECT * FROM game_records WHERE timestamp BETWEEN :startTime AND :endTime ORDER BY timestamp DESC")
    fun getGameRecordsByDateRange(startTime: Long, endTime: Long): Flow<List<GameRecordEntity>>
    
    /**
     * Delete a specific game record
     */
    @Delete
    suspend fun deleteGameRecord(gameRecord: GameRecordEntity)
    
    /**
     * Delete all game records
     */
    @Query("DELETE FROM game_records")
    suspend fun deleteAllGameRecords()
    
    /**
     * Delete old game records, keeping only the most recent ones
     */
    @Query("DELETE FROM game_records WHERE id NOT IN (SELECT id FROM game_records ORDER BY timestamp DESC LIMIT :keepCount)")
    suspend fun deleteOldGameRecords(keepCount: Int)
}