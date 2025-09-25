package com.example.ntagapp.animation

import androidx.compose.animation.core.*
import androidx.compose.foundation.layout.offset
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.alpha
import androidx.compose.ui.draw.rotate
import androidx.compose.ui.draw.scale
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.unit.dp
import com.example.ntagapp.model.AnimationState
import kotlinx.coroutines.delay

/**
 * Manager for handling various animations in the game
 */
class AnimationManager {
    
    /**
     * Create bounce animation for buttons
     */
    @Composable
    fun createBounceAnimation(trigger: Boolean): Float {
        val scale by animateFloatAsState(
            targetValue = if (trigger) 0.95f else 1.0f,
            animationSpec = spring(
                dampingRatio = Spring.DampingRatioMediumBouncy,
                stiffness = Spring.StiffnessLow
            ),
            label = "bounce_animation"
        )
        return scale
    }
    
    /**
     * Create fade in/out animation
     */
    @Composable
    fun createFadeAnimation(visible: Boolean, duration: Int = 300): Float {
        val alpha by animateFloatAsState(
            targetValue = if (visible) 1.0f else 0.0f,
            animationSpec = tween(durationMillis = duration),
            label = "fade_animation"
        )
        return alpha
    }
    
    /**
     * Create slide animation
     */
    @Composable
    fun createSlideAnimation(visible: Boolean, fromLeft: Boolean = true): Float {
        val offset by animateFloatAsState(
            targetValue = if (visible) 0f else if (fromLeft) -100f else 100f,
            animationSpec = spring(
                dampingRatio = Spring.DampingRatioMediumBouncy,
                stiffness = Spring.StiffnessMedium
            ),
            label = "slide_animation"
        )
        return offset
    }
    
    /**
     * Create rotation animation for thinking state
     */
    @Composable
    fun createRotationAnimation(isRotating: Boolean): Float {
        val infiniteTransition = rememberInfiniteTransition(label = "rotation_transition")
        val rotation by infiniteTransition.animateFloat(
            initialValue = 0f,
            targetValue = if (isRotating) 360f else 0f,
            animationSpec = infiniteRepeatable(
                animation = tween(durationMillis = 2000, easing = LinearEasing),
                repeatMode = RepeatMode.Restart
            ),
            label = "rotation_animation"
        )
        return rotation
    }
    
    /**
     * Create pulsing animation for highlighting
     */
    @Composable
    fun createPulseAnimation(isPulsing: Boolean): Float {
        val infiniteTransition = rememberInfiniteTransition(label = "pulse_transition")
        val scale by infiniteTransition.animateFloat(
            initialValue = 1.0f,
            targetValue = if (isPulsing) 1.1f else 1.0f,
            animationSpec = infiniteRepeatable(
                animation = tween(durationMillis = 1000, easing = FastOutSlowInEasing),
                repeatMode = RepeatMode.Reverse
            ),
            label = "pulse_animation"
        )
        return scale
    }
    
    /**
     * Create shake animation for wrong actions
     */
    @Composable
    fun createShakeAnimation(trigger: Boolean): Float {
        val infiniteTransition = rememberInfiniteTransition(label = "shake_transition")
        val shake by infiniteTransition.animateFloat(
            initialValue = 0f,
            targetValue = if (trigger) 10f else 0f,
            animationSpec = infiniteRepeatable(
                animation = tween(durationMillis = 100, easing = LinearEasing),
                repeatMode = RepeatMode.Reverse
            ),
            label = "shake_animation"
        )
        return shake
    }
    
    /**
     * Create celebration animation for wins
     */
    @Composable
    fun createCelebrationAnimation(trigger: Boolean): AnimationValues {
        val scale by animateFloatAsState(
            targetValue = if (trigger) 1.2f else 1.0f,
            animationSpec = spring(
                dampingRatio = Spring.DampingRatioMediumBouncy,
                stiffness = Spring.StiffnessLow
            ),
            label = "celebration_scale"
        )
        
        val rotation by animateFloatAsState(
            targetValue = if (trigger) 360f else 0f,
            animationSpec = tween(durationMillis = 1000, easing = FastOutSlowInEasing),
            label = "celebration_rotation"
        )
        
        return AnimationValues(scale = scale, rotation = rotation)
    }
    
    /**
     * Create typing animation for text
     */
    @Composable
    fun createTypingAnimation(text: String, isTyping: Boolean): String {
        var displayText by remember { mutableStateOf("") }
        
        LaunchedEffect(text, isTyping) {
            if (isTyping && text.isNotEmpty()) {
                displayText = ""
                text.forEachIndexed { index, _ ->
                    delay(50) // Typing speed
                    displayText = text.substring(0, index + 1)
                }
            } else {
                displayText = text
            }
        }
        
        return displayText
    }
    
    /**
     * Create floating animation for pet
     */
    @Composable
    fun createFloatingAnimation(isFloating: Boolean): Float {
        val infiniteTransition = rememberInfiniteTransition(label = "floating_transition")
        val offset by infiniteTransition.animateFloat(
            initialValue = 0f,
            targetValue = if (isFloating) 10f else 0f,
            animationSpec = infiniteRepeatable(
                animation = tween(durationMillis = 2000, easing = FastOutSlowInEasing),
                repeatMode = RepeatMode.Reverse
            ),
            label = "floating_animation"
        )
        return offset
    }
    
    /**
     * Get animation modifier based on animation state
     */
    @Composable
    fun getAnimationModifier(animationState: AnimationState): Modifier {
        return when (animationState) {
            AnimationState.IDLE -> Modifier
            AnimationState.USER_SELECTING -> {
                val scale = createBounceAnimation(true)
                Modifier.scale(scale)
            }
            AnimationState.DEVICE_THINKING -> {
                val rotation = createRotationAnimation(true)
                val pulse = createPulseAnimation(true)
                Modifier
                    .rotate(rotation)
                    .scale(pulse)
            }
            AnimationState.SHOWING_RESULT -> {
                val celebration = createCelebrationAnimation(true)
                Modifier
                    .scale(celebration.scale)
                    .rotate(celebration.rotation)
            }
            AnimationState.CELEBRATING -> {
                val celebration = createCelebrationAnimation(true)
                Modifier
                    .scale(celebration.scale)
                    .rotate(celebration.rotation)
            }
            AnimationState.DISAPPOINTED -> {
                val scale = createBounceAnimation(false)
                Modifier.scale(scale)
            }
            AnimationState.NEUTRAL -> Modifier
        }
    }
}

/**
 * Data class to hold multiple animation values
 */
data class AnimationValues(
    val scale: Float = 1.0f,
    val rotation: Float = 0.0f,
    val alpha: Float = 1.0f,
    val offsetX: Float = 0.0f,
    val offsetY: Float = 0.0f
)

/**
 * Extension functions for applying animations to Modifier
 */
fun Modifier.animatedScale(scale: Float): Modifier = this.scale(scale)
fun Modifier.animatedRotation(rotation: Float): Modifier = this.rotate(rotation)
fun Modifier.animatedAlpha(alpha: Float): Modifier = this.alpha(alpha)
fun Modifier.animatedOffset(x: Float, y: Float): Modifier = this.offset(x.dp, y.dp)