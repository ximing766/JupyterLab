package com.example.ntagapp.viewmodel

import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewModelScope
import com.example.ntagapp.model.GameChoice
import com.example.ntagapp.model.GameRecord
import com.example.ntagapp.model.GameResult
import com.example.ntagapp.model.GameStatistics
import com.example.ntagapp.repository.GameRepository
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

/**
 * ViewModel for managing game statistics and history
 */
class StatisticsViewModel(private val gameRepository: GameRepository) : ViewModel() {
    
    private val _statistics = MutableStateFlow(GameStatistics())
    val statistics: StateFlow<GameStatistics> = _statistics.asStateFlow()
    
    private val _gameHistory = MutableStateFlow<List<GameRecord>>(emptyList())
    val gameHistory: StateFlow<List<GameRecord>> = _gameHistory.asStateFlow()
    
    private val _isLoading = MutableStateFlow(false)
    val isLoading: StateFlow<Boolean> = _isLoading.asStateFlow()
    
    private val _choiceStatistics = MutableStateFlow<Map<GameChoice, Int>>(emptyMap())
    val choiceStatistics: StateFlow<Map<GameChoice, Int>> = _choiceStatistics.asStateFlow()
    
    init {
        loadStatistics()
        loadGameHistory()
    }
    
    /**
     * Load game statistics from repository
     */
    fun loadStatistics() {
        viewModelScope.launch {
            _isLoading.value = true
            try {
                val stats = gameRepository.getGameStatistics()
                _statistics.value = stats
                
                // Load choice statistics
                loadChoiceStatistics()
                
            } catch (e: Exception) {
                // Handle error
            } finally {
                _isLoading.value = false
            }
        }
    }
    
    /**
     * Load game history from repository
     */
    private fun loadGameHistory() {
        viewModelScope.launch {
            try {
                gameRepository.getAllGameRecords().collect { records ->
                    _gameHistory.value = records
                }
            } catch (e: Exception) {
                // Handle error
            }
        }
    }
    
    /**
     * Load choice statistics (how often each choice was used)
     */
    private fun loadChoiceStatistics() {
        viewModelScope.launch {
            try {
                val history = _gameHistory.value
                val choiceCount = mutableMapOf<GameChoice, Int>()
                
                GameChoice.values().forEach { choice ->
                    choiceCount[choice] = history.count { it.userChoice == choice }
                }
                
                _choiceStatistics.value = choiceCount
            } catch (e: Exception) {
                // Handle error
            }
        }
    }
    
    /**
     * Get win rate as formatted string
     */
    fun getWinRateString(): String {
        return _statistics.value.getFormattedWinRate()
    }
    
    /**
     * Get lose rate as formatted string
     */
    fun getLoseRateString(): String {
        return _statistics.value.getFormattedLoseRate()
    }
    
    /**
     * Get draw rate as formatted string
     */
    fun getDrawRateString(): String {
        return _statistics.value.getFormattedDrawRate()
    }
    
    /**
     * Get most used choice
     */
    fun getMostUsedChoice(): GameChoice? {
        return _choiceStatistics.value.maxByOrNull { it.value }?.key
    }
    
    /**
     * Get least used choice
     */
    fun getLeastUsedChoice(): GameChoice? {
        return _choiceStatistics.value.minByOrNull { it.value }?.key
    }
    
    /**
     * Get choice usage percentage
     */
    fun getChoiceUsagePercentage(choice: GameChoice): Float {
        val total = _statistics.value.totalGames
        if (total == 0) return 0f
        
        val count = _choiceStatistics.value[choice] ?: 0
        return (count.toFloat() / total.toFloat()) * 100f
    }
    
    /**
     * Get recent games (last N games)
     */
    fun getRecentGames(limit: Int = 10): List<GameRecord> {
        return _gameHistory.value.take(limit)
    }
    
    /**
     * Get games by result type
     */
    fun getGamesByResult(result: GameResult): List<GameRecord> {
        return _gameHistory.value.filter { it.result == result }
    }
    
    /**
     * Get games by choice
     */
    fun getGamesByChoice(choice: GameChoice): List<GameRecord> {
        return _gameHistory.value.filter { it.userChoice == choice }
    }
    
    /**
     * Get performance summary text
     */
    fun getPerformanceSummary(): String {
        val stats = _statistics.value
        return when {
            stats.totalGames == 0 -> "还没有游戏记录"
            stats.winRate > 60f -> "表现优秀！胜率超过60%"
            stats.winRate > 40f -> "表现不错，继续加油！"
            else -> "需要更多练习，加油！"
        }
    }
    
    /**
     * Get streak summary text
     */
    fun getStreakSummary(): String {
        val stats = _statistics.value
        return when {
            stats.maxWinStreak > 5 -> "最高连胜${stats.maxWinStreak}场，太厉害了！"
            stats.maxWinStreak > 0 -> "最高连胜${stats.maxWinStreak}场"
            else -> "还没有连胜记录"
        }
    }
    
    /**
     * Get choice distribution summary
     */
    fun getChoiceDistributionSummary(): String {
        val mostUsed = getMostUsedChoice()
        val leastUsed = getLeastUsedChoice()
        
        return when {
            mostUsed == null -> "还没有选择记录"
            mostUsed == leastUsed -> "各种选择使用均衡"
            else -> "最常用：${mostUsed.getDisplayName()} ${mostUsed.getEmoji()}"
        }
    }
    
    /**
     * Clear all statistics and game history
     */
    fun clearAllData() {
        viewModelScope.launch {
            try {
                gameRepository.clearAllGameRecords()
                loadStatistics()
                loadGameHistory()
            } catch (e: Exception) {
                // Handle error
            }
        }
    }
    
    /**
     * Refresh all data
     */
    fun refreshData() {
        loadStatistics()
        loadGameHistory()
    }
    
    /**
     * Get total play time estimation (based on average game duration)
     */
    fun getEstimatedPlayTime(): String {
        val totalGames = _statistics.value.totalGames
        val estimatedMinutes = totalGames * 0.5 // Assume 30 seconds per game
        
        return when {
            estimatedMinutes < 1 -> "少于1分钟"
            estimatedMinutes < 60 -> "约${estimatedMinutes.toInt()}分钟"
            else -> "约${(estimatedMinutes / 60).toInt()}小时${(estimatedMinutes % 60).toInt()}分钟"
        }
    }
}

/**
 * Factory for creating StatisticsViewModel with dependencies
 */
class StatisticsViewModelFactory(private val gameRepository: GameRepository) : ViewModelProvider.Factory {
    @Suppress("UNCHECKED_CAST")
    override fun <T : ViewModel> create(modelClass: Class<T>): T {
        if (modelClass.isAssignableFrom(StatisticsViewModel::class.java)) {
            return StatisticsViewModel(gameRepository) as T
        }
        throw IllegalArgumentException("Unknown ViewModel class")
    }
}