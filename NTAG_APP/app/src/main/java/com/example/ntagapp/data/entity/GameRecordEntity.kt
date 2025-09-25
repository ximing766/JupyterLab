package com.example.ntagapp.data.entity

import androidx.room.ColumnInfo
import androidx.room.Entity
import androidx.room.PrimaryKey
import com.example.ntagapp.model.GameChoice
import com.example.ntagapp.model.GameRecord
import com.example.ntagapp.model.GameResult

/**
 * Room entity for storing game records in the database
 */
@Entity(tableName = "game_records")
data class GameRecordEntity(
    @PrimaryKey(autoGenerate = true)
    val id: Long = 0,
    
    @ColumnInfo(name = "user_choice")
    val userChoice: String,
    
    @ColumnInfo(name = "device_choice")
    val deviceChoice: String,
    
    val result: String,
    
    val timestamp: Long
) {
    /**
     * Convert entity to domain model
     */
    fun toDomainModel(): GameRecord {
        return GameRecord(
            id = id,
            userChoice = GameChoice.valueOf(userChoice),
            deviceChoice = GameChoice.valueOf(deviceChoice),
            result = GameResult.valueOf(result),
            timestamp = timestamp
        )
    }
    
    companion object {
        /**
         * Create entity from domain model
         */
        fun fromDomainModel(gameRecord: GameRecord): GameRecordEntity {
            return GameRecordEntity(
                id = gameRecord.id,
                userChoice = gameRecord.userChoice.name,
                deviceChoice = gameRecord.deviceChoice.name,
                result = gameRecord.result.name,
                timestamp = gameRecord.timestamp
            )
        }
    }
}