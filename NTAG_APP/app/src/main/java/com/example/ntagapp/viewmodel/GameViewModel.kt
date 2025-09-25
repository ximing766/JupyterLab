package com.example.ntagapp.viewmodel

import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewModelScope
import com.example.ntagapp.audio.AudioManager
import com.example.ntagapp.repository.GameRepository
import com.example.ntagapp.logic.GameLogic
import com.example.ntagapp.model.*
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

/**
 * ViewModel for managing game state and logic
 */
class GameViewModel(
    private val repository: GameRepository,
    private val audioManager: AudioManager
) : ViewModel() {
    
    private val gameLogic = GameLogic()
    
    private val _gameState = MutableStateFlow(GameState())
    val gameState: StateFlow<GameState> = _gameState.asStateFlow()
    
    private val _recentGames = MutableStateFlow<List<GameRecord>>(emptyList())
    val recentGames: StateFlow<List<GameRecord>> = _recentGames.asStateFlow()
    
    init {
        loadRecentGames()
    }
    
    /**
     * Play a game with the given user choice
     */
    fun playGame(userChoice: GameChoice) {
        viewModelScope.launch {
            _gameState.value = _gameState.value.copy(
                isLoading = true,
                userChoice = userChoice,
                animationState = AnimationState.DEVICE_THINKING
            )
            
            // Play click sound
            audioManager.playSound(AudioManager.SoundType.CLICK)
            
            // Simulate thinking time
            delay(1000)
            
            // Generate device choice using simplified game logic
            val deviceChoice = gameLogic.generateDeviceChoice()
            
            // Determine result using game logic
            val result = gameLogic.determineResult(userChoice, deviceChoice)
            
            // Update state with result
            _gameState.value = _gameState.value.copy(
                isLoading = false,
                deviceChoice = deviceChoice,
                result = result,
                animationState = when (result) {
                    GameResult.WIN -> AnimationState.CELEBRATING
                    GameResult.LOSE -> AnimationState.DISAPPOINTED
                    GameResult.DRAW -> AnimationState.NEUTRAL
                }
            )
            
            // Play result sound
            when (result) {
                GameResult.WIN -> {
                    audioManager.playSound(AudioManager.SoundType.WIN)
                    updateScore(true)
                }
                GameResult.LOSE -> {
                    audioManager.playSound(AudioManager.SoundType.LOSE)
                }
                GameResult.DRAW -> {
                    audioManager.playSound(AudioManager.SoundType.DRAW)
                }
            }
            
            // Save game record
            val gameRecord = GameRecord(
                userChoice = userChoice,
                deviceChoice = deviceChoice,
                result = result,
                timestamp = System.currentTimeMillis()
            )
            
            repository.saveGameRecord(gameRecord)
            loadRecentGames()
            
            // Reset animation after delay
            delay(3000)
            _gameState.value = _gameState.value.copy(
                animationState = AnimationState.IDLE
            )
        }
    }
    
    /**
     * Reset game scores
     */
    fun resetScore() {
        viewModelScope.launch {
            repository.clearAllGameRecords()
            _gameState.value = _gameState.value.copy(
                score = 0
            )
        }
    }
    
    /**
     * Clear all game history
     */
    fun clearGameHistory() {
        viewModelScope.launch {
            try {
                repository.clearAllGameRecords()
                resetScore()
                loadRecentGames()
            } catch (e: Exception) {
                // Handle error silently or show error message
            }
        }
    }
    
    /**
     * Load recent games from repository
     */
    private fun loadRecentGames() {
        viewModelScope.launch {
            try {
                val recentGames = repository.getRecentGameRecords(5)
                recentGames.collect { games ->
                    _recentGames.value = games
                }
            } catch (e: Exception) {
                // Handle error silently or show error state
            }
        }
    }
    
    /**
     * Update user score
     */
    private fun updateScore(won: Boolean) {
        if (won) {
            _gameState.value = _gameState.value.copy(
                score = _gameState.value.score + 1
            )
        }
    }
    
    /**
     * Get game statistics
     */
    suspend fun getGameStatistics() = repository.getGameStatistics()
    
    /**
     * Get choice statistics - placeholder implementation
     */
    fun getChoiceStatistics(): Map<GameChoice, Int> {
        // This would typically come from the repository
        // For now, return empty map as placeholder
        return emptyMap()
    }
    
    /**
     * Get current game statistics summary
     */
    fun getGameSummary(): String {
        val state = _gameState.value
        return "得分: ${state.score} | 连胜: ${maxOf(0, state.currentStreak)}"
    }
    
    /**
     * Check if user is on a winning streak
     */
    fun isOnWinningStreak(): Boolean {
        return _gameState.value.currentStreak > 0
    }
    
    /**
     * Check if user is on a losing streak
     */
    fun isOnLosingStreak(): Boolean {
        return _gameState.value.currentStreak < 0
    }
    
    /**
     * Get streak description for UI
     */
    fun getStreakDescription(): String {
        val streak = _gameState.value.currentStreak
        return when {
            streak > 0 -> "连胜 $streak 场!"
            streak < 0 -> "连败 ${-streak} 场"
            else -> "平局状态"
        }
    }
}

/**
 * Factory for creating GameViewModel with dependencies
 */
class GameViewModelFactory(
    private val gameRepository: GameRepository,
    private val audioManager: AudioManager
) : ViewModelProvider.Factory {
    @Suppress("UNCHECKED_CAST")
    override fun <T : ViewModel> create(modelClass: Class<T>): T {
        if (modelClass.isAssignableFrom(GameViewModel::class.java)) {
            return GameViewModel(gameRepository, audioManager) as T
        }
        throw IllegalArgumentException("Unknown ViewModel class")
    }
}