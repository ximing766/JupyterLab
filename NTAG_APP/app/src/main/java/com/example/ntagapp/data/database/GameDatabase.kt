package com.example.ntagapp.data.database

import androidx.room.Database
import androidx.room.Room
import androidx.room.RoomDatabase
import androidx.room.migration.Migration
import androidx.sqlite.db.SupportSQLiteDatabase
import android.content.Context
import com.example.ntagapp.data.dao.GameRecordDao
import com.example.ntagapp.data.entity.GameRecordEntity

/**
 * Room database for the Rock-Paper-Scissors game
 */
@Database(
    entities = [GameRecordEntity::class],
    version = 1,
    exportSchema = false
)
abstract class GameDatabase : RoomDatabase() {
    
    abstract fun gameRecordDao(): GameRecordDao
    
    companion object {
        @Volatile
        private var INSTANCE: GameDatabase? = null
        
        private const val DATABASE_NAME = "game_database"
        
        /**
         * Get database instance using singleton pattern
         */
        fun getDatabase(context: Context): GameDatabase {
            return INSTANCE ?: synchronized(this) {
                val instance = Room.databaseBuilder(
                    context.applicationContext,
                    GameDatabase::class.java,
                    DATABASE_NAME
                )
                    .addCallback(DatabaseCallback())
                    .build()
                INSTANCE = instance
                instance
            }
        }
        
        /**
         * Database callback for initialization
         */
        private class DatabaseCallback : RoomDatabase.Callback() {
            override fun onCreate(db: SupportSQLiteDatabase) {
                super.onCreate(db)
                // Create indexes for better performance
                db.execSQL("CREATE INDEX IF NOT EXISTS idx_game_records_timestamp ON game_records(timestamp DESC)")
                db.execSQL("CREATE INDEX IF NOT EXISTS idx_game_records_result ON game_records(result)")
            }
        }
        
        /**
         * Migration from version 1 to 2 (for future use)
         */
        val MIGRATION_1_2 = object : Migration(1, 2) {
            override fun migrate(database: SupportSQLiteDatabase) {
                // Add migration logic here when needed
            }
        }
    }
}