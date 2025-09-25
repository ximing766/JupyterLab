package com.example.ntagapp.model

/**
 * Enum representing different types of electronic pets
 */
enum class PetType {
    DEFAULT,
    CAT,
    DOG,
    ROBOT;
    
    /**
     * Get display name for the pet type
     */
    fun getDisplayName(): String {
        return when (this) {
            DEFAULT -> "默认宠物"
            CAT -> "小猫咪"
            DOG -> "小狗狗"
            ROBOT -> "机器人"
        }
    }
    
    /**
     * Get emoji representation for the pet type
     */
    fun getEmoji(): String {
        return when (this) {
            DEFAULT -> "🐾"
            CAT -> "🐱"
            DOG -> "🐶"
            ROBOT -> "🤖"
        }
    }
    
    /**
     * Get animation set identifier for the pet type
     */
    fun getAnimationSet(): String {
        return when (this) {
            DEFAULT -> "default_animations"
            CAT -> "cat_animations"
            DOG -> "dog_animations"
            ROBOT -> "robot_animations"
        }
    }
}