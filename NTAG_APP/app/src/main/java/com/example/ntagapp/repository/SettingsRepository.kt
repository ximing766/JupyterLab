package com.example.ntagapp.repository

import android.content.Context
import androidx.datastore.core.DataStore
import androidx.datastore.preferences.core.Preferences
import androidx.datastore.preferences.core.booleanPreferencesKey
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.stringPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import com.example.ntagapp.model.AnimationSpeed
import com.example.ntagapp.model.AppSettings
import com.example.ntagapp.model.PetType
import com.example.ntagapp.model.ThemeMode
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map

/**
 * Repository for handling application settings
 */
class SettingsRepository(private val context: Context) {
    
    companion object {
        private val Context.dataStore: DataStore<Preferences> by preferencesDataStore(name = "settings")
        
        // Preference keys
        private val SOUND_ENABLED = booleanPreferencesKey("sound_enabled")
        private val PET_ENABLED = booleanPreferencesKey("pet_enabled")
        private val SELECTED_PET_TYPE = stringPreferencesKey("selected_pet_type")
        private val VIBRATION_ENABLED = booleanPreferencesKey("vibration_enabled")
        private val ANIMATION_SPEED = stringPreferencesKey("animation_speed")
        private val THEME_MODE = stringPreferencesKey("theme_mode")
    }
    
    /**
     * Get app settings as Flow
     */
    val appSettings: Flow<AppSettings> = context.dataStore.data.map { preferences ->
        AppSettings(
            soundEnabled = preferences[SOUND_ENABLED] ?: true,
            petEnabled = preferences[PET_ENABLED] ?: true,
            selectedPetType = try {
                PetType.valueOf(preferences[SELECTED_PET_TYPE] ?: PetType.ROBOT.name)
            } catch (e: IllegalArgumentException) {
                PetType.ROBOT
            },
            vibrationEnabled = preferences[VIBRATION_ENABLED] ?: true,
            animationSpeed = try {
                AnimationSpeed.valueOf(preferences[ANIMATION_SPEED] ?: AnimationSpeed.NORMAL.name)
            } catch (e: IllegalArgumentException) {
                AnimationSpeed.NORMAL
            },
            themeMode = try {
                ThemeMode.valueOf(preferences[THEME_MODE] ?: ThemeMode.SYSTEM.name)
            } catch (e: IllegalArgumentException) {
                ThemeMode.SYSTEM
            }
        )
    }
    
    /**
     * Update sound enabled setting
     */
    suspend fun setSoundEnabled(enabled: Boolean) {
        context.dataStore.edit { preferences ->
            preferences[SOUND_ENABLED] = enabled
        }
    }
    
    /**
     * Update pet enabled setting
     */
    suspend fun setPetEnabled(enabled: Boolean) {
        context.dataStore.edit { preferences ->
            preferences[PET_ENABLED] = enabled
        }
    }
    
    /**
     * Update selected pet type
     */
    suspend fun setSelectedPetType(petType: PetType) {
        context.dataStore.edit { preferences ->
            preferences[SELECTED_PET_TYPE] = petType.name
        }
    }
    
    /**
     * Update vibration enabled setting
     */
    suspend fun setVibrationEnabled(enabled: Boolean) {
        context.dataStore.edit { preferences ->
            preferences[VIBRATION_ENABLED] = enabled
        }
    }
    
    /**
     * Update animation speed setting
     */
    suspend fun setAnimationSpeed(speed: AnimationSpeed) {
        context.dataStore.edit { preferences ->
            preferences[ANIMATION_SPEED] = speed.name
        }
    }
    
    /**
     * Update theme mode setting
     */
    suspend fun setThemeMode(mode: ThemeMode) {
        context.dataStore.edit { preferences ->
            preferences[THEME_MODE] = mode.name
        }
    }
    
    /**
     * Reset all settings to default values
     */
    suspend fun resetToDefaults() {
        context.dataStore.edit { preferences ->
            preferences.clear()
        }
    }
    
    /**
     * Update multiple settings at once
     */
    suspend fun updateSettings(settings: AppSettings) {
        context.dataStore.edit { preferences ->
            preferences[SOUND_ENABLED] = settings.soundEnabled
            preferences[PET_ENABLED] = settings.petEnabled
            preferences[SELECTED_PET_TYPE] = settings.selectedPetType.name
            preferences[VIBRATION_ENABLED] = settings.vibrationEnabled
            preferences[ANIMATION_SPEED] = settings.animationSpeed.name
            preferences[THEME_MODE] = settings.themeMode.name
        }
    }
}