package com.example.ntagapp.viewmodel

import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewModelScope
import com.example.ntagapp.model.AnimationSpeed
import com.example.ntagapp.model.AppSettings
import com.example.ntagapp.model.PetType
import com.example.ntagapp.model.ThemeMode
import com.example.ntagapp.repository.SettingsRepository
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

/**
 * ViewModel for managing application settings
 */
class SettingsViewModel(private val settingsRepository: SettingsRepository) : ViewModel() {
    
    private val _settings = MutableStateFlow(AppSettings())
    val settings: StateFlow<AppSettings> = _settings.asStateFlow()
    
    private val _isLoading = MutableStateFlow(false)
    val isLoading: StateFlow<Boolean> = _isLoading.asStateFlow()
    
    init {
        loadSettings()
    }
    
    /**
     * Load settings from repository
     */
    private fun loadSettings() {
        viewModelScope.launch {
            _isLoading.value = true
            try {
                settingsRepository.appSettings.collect { settings ->
                    _settings.value = settings
                    _isLoading.value = false
                }
            } catch (e: Exception) {
                _isLoading.value = false
                // Handle error - could emit error state or use default settings
            }
        }
    }
    
    /**
     * Toggle sound enabled setting
     */
    fun toggleSound() {
        viewModelScope.launch {
            try {
                val newValue = !_settings.value.soundEnabled
                settingsRepository.setSoundEnabled(newValue)
            } catch (e: Exception) {
                // Handle error
            }
        }
    }
    
    /**
     * Set sound enabled setting
     */
    fun setSoundEnabled(enabled: Boolean) {
        viewModelScope.launch {
            try {
                settingsRepository.setSoundEnabled(enabled)
            } catch (e: Exception) {
                // Handle error
            }
        }
    }
    
    /**
     * Toggle pet enabled setting
     */
    fun togglePet() {
        viewModelScope.launch {
            try {
                val newValue = !_settings.value.petEnabled
                settingsRepository.setPetEnabled(newValue)
            } catch (e: Exception) {
                // Handle error
            }
        }
    }
    
    /**
     * Set pet enabled setting
     */
    fun setPetEnabled(enabled: Boolean) {
        viewModelScope.launch {
            try {
                settingsRepository.setPetEnabled(enabled)
            } catch (e: Exception) {
                // Handle error
            }
        }
    }
    
    /**
     * Set selected pet type
     */
    fun setSelectedPetType(petType: PetType) {
        viewModelScope.launch {
            try {
                settingsRepository.setSelectedPetType(petType)
            } catch (e: Exception) {
                // Handle error
            }
        }
    }
    
    /**
     * Toggle vibration enabled setting
     */
    fun toggleVibration() {
        viewModelScope.launch {
            try {
                val newValue = !_settings.value.vibrationEnabled
                settingsRepository.setVibrationEnabled(newValue)
            } catch (e: Exception) {
                // Handle error
            }
        }
    }
    
    /**
     * Set vibration enabled setting
     */
    fun setVibrationEnabled(enabled: Boolean) {
        viewModelScope.launch {
            try {
                settingsRepository.setVibrationEnabled(enabled)
            } catch (e: Exception) {
                // Handle error
            }
        }
    }
    
    /**
     * Set animation speed
     */
    fun setAnimationSpeed(speed: AnimationSpeed) {
        viewModelScope.launch {
            try {
                settingsRepository.setAnimationSpeed(speed)
            } catch (e: Exception) {
                // Handle error
            }
        }
    }
    
    /**
     * Set theme mode
     */
    fun setThemeMode(mode: ThemeMode) {
        viewModelScope.launch {
            try {
                settingsRepository.setThemeMode(mode)
            } catch (e: Exception) {
                // Handle error
            }
        }
    }
    
    /**
     * Reset all settings to default values
     */
    fun resetToDefaults() {
        viewModelScope.launch {
            try {
                settingsRepository.resetToDefaults()
            } catch (e: Exception) {
                // Handle error
            }
        }
    }
    
    /**
     * Get available pet types
     */
    fun getAvailablePetTypes(): List<PetType> {
        return PetType.values().toList()
    }
    
    /**
     * Get available animation speeds
     */
    fun getAvailableAnimationSpeeds(): List<AnimationSpeed> {
        return AnimationSpeed.values().toList()
    }
    
    /**
     * Get available theme modes
     */
    fun getAvailableThemeModes(): List<ThemeMode> {
        return ThemeMode.values().toList()
    }
    
    /**
     * Get current pet type display name
     */
    fun getCurrentPetDisplayName(): String {
        return _settings.value.selectedPetType.getDisplayName()
    }
    
    /**
     * Get current pet emoji
     */
    fun getCurrentPetEmoji(): String {
        return _settings.value.selectedPetType.getEmoji()
    }
    
    /**
     * Get animation speed multiplier for UI animations
     */
    fun getAnimationSpeedMultiplier(): Float {
        return when (_settings.value.animationSpeed) {
            AnimationSpeed.SLOW -> 1.5f
            AnimationSpeed.NORMAL -> 1.0f
            AnimationSpeed.FAST -> 0.7f
        }
    }
    
    /**
     * Check if dark theme should be used
     */
    fun shouldUseDarkTheme(isSystemInDarkTheme: Boolean): Boolean {
        return when (_settings.value.themeMode) {
            ThemeMode.LIGHT -> false
            ThemeMode.DARK -> true
            ThemeMode.SYSTEM -> isSystemInDarkTheme
        }
    }
}

/**
 * Factory for creating SettingsViewModel with dependencies
 */
class SettingsViewModelFactory(private val settingsRepository: SettingsRepository) : ViewModelProvider.Factory {
    @Suppress("UNCHECKED_CAST")
    override fun <T : ViewModel> create(modelClass: Class<T>): T {
        if (modelClass.isAssignableFrom(SettingsViewModel::class.java)) {
            return SettingsViewModel(settingsRepository) as T
        }
        throw IllegalArgumentException("Unknown ViewModel class")
    }
}