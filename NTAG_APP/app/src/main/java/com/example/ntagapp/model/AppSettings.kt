package com.example.ntagapp.model

/**
 * Data class representing application settings
 */
data class AppSettings(
    val soundEnabled: Boolean = true,
    val petEnabled: Boolean = true,
    val selectedPetType: PetType = PetType.ROBOT,
    val vibrationEnabled: Boolean = true,
    val animationSpeed: AnimationSpeed = AnimationSpeed.NORMAL,
    val themeMode: ThemeMode = ThemeMode.SYSTEM
) {
    companion object {
        // Default settings instance
        val DEFAULT = AppSettings()
    }
}

/**
 * Enum representing animation speed options
 */
enum class AnimationSpeed(val multiplier: Float) {
    SLOW(0.5f),
    NORMAL(1.0f),
    FAST(1.5f);
    
    fun getDisplayName(): String {
        return when (this) {
            SLOW -> "慢速"
            NORMAL -> "正常"
            FAST -> "快速"
        }
    }
}

/**
 * Enum representing theme mode options
 */
enum class ThemeMode {
    LIGHT,
    DARK,
    SYSTEM;
    
    fun getDisplayName(): String {
        return when (this) {
            LIGHT -> "浅色模式"
            DARK -> "深色模式"
            SYSTEM -> "跟随系统"
        }
    }
}