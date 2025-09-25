package com.example.ntagapp.ui.components

import androidx.compose.animation.core.*
import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.gestures.detectTapGestures
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.alpha
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.rotate
import androidx.compose.ui.draw.scale
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.ntagapp.R
import com.example.ntagapp.model.AnimationState
import com.example.ntagapp.animation.AnimationManager
import com.example.ntagapp.model.*

/**
 * Score board component
 */
@Composable
fun ScoreBoard(
    userScore: Int,
    deviceScore: Int,
    modifier: Modifier = Modifier
) {
    Card(
        modifier = modifier.fillMaxWidth(),
        shape = RoundedCornerShape(16.dp),
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.colorScheme.primaryContainer
        ),
        elevation = CardDefaults.cardElevation(defaultElevation = 8.dp)
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(24.dp),
            horizontalArrangement = Arrangement.SpaceEvenly,
            verticalAlignment = Alignment.CenterVertically
        ) {
            // User Score
            ScoreItem(
                label = "你",
                score = userScore,
                color = MaterialTheme.colorScheme.primary
            )
            
            // VS Divider
            Text(
                text = "VS",
                style = MaterialTheme.typography.headlineSmall,
                fontWeight = FontWeight.Bold,
                color = MaterialTheme.colorScheme.onPrimaryContainer
            )
            
            // Device Score
            ScoreItem(
                label = "设备",
                score = deviceScore,
                color = MaterialTheme.colorScheme.secondary
            )
        }
    }
}

@Composable
fun ScoreItem(
    label: String,
    score: Int,
    color: Color,
    modifier: Modifier = Modifier
) {
    Column(
        horizontalAlignment = Alignment.CenterHorizontally,
        modifier = modifier
    ) {
        Text(
            text = score.toString(),
            style = MaterialTheme.typography.displayMedium,
            fontWeight = FontWeight.Bold,
            color = color
        )
        Text(
            text = label,
            style = MaterialTheme.typography.bodyLarge,
            color = MaterialTheme.colorScheme.onPrimaryContainer
        )
    }
}

/**
 * Game result display showing user and device choices with result
 */
@Composable
fun GameResultDisplay(
    gameState: GameState,
    petType: PetType = PetType.ROBOT,
    modifier: Modifier = Modifier
) {
    // Animation states
    val showResult = gameState.result != null
    val isThinking = gameState.animationState == AnimationState.DEVICE_THINKING
    val isWin = gameState.result == GameResult.WIN
    
    // Simple animations
    val resultAlpha by animateFloatAsState(
        targetValue = if (showResult) 1f else 0.7f,
        animationSpec = tween(300),
        label = "result_alpha"
    )
    val scale by animateFloatAsState(
        targetValue = if (isWin) 1.1f else 1f,
        animationSpec = tween(300),
        label = "celebration_scale"
    )
    
    Column(
        modifier = modifier
            .fillMaxWidth()
            .padding(16.dp),
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        // Result text with fade animation
        Text(
            text = when (gameState.result) {
                GameResult.WIN -> "你赢了！"
                GameResult.LOSE -> "你输了！"
                GameResult.DRAW -> "平局！"
                null -> if (isThinking) "思考中..." else "选择你的出招"
            },
            style = MaterialTheme.typography.headlineMedium,
            fontWeight = FontWeight.Bold,
            color = when (gameState.result) {
                GameResult.WIN -> Color(0xFF4CAF50)
                GameResult.LOSE -> Color(0xFFF44336)
                GameResult.DRAW -> Color(0xFFFF9800)
                null -> MaterialTheme.colorScheme.onSurface
            },
            modifier = Modifier
                .padding(bottom = 24.dp)
                .alpha(resultAlpha)
                .scale(scale)
        )
        
        // Choices display
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceEvenly,
            verticalAlignment = Alignment.CenterVertically
        ) {
            // User choice with animation
            Column(
                horizontalAlignment = Alignment.CenterHorizontally
            ) {
                Text(
                    text = "你",
                    style = MaterialTheme.typography.titleMedium,
                    fontWeight = FontWeight.Medium
                )
                Spacer(modifier = Modifier.height(8.dp))
                
                if (gameState.userChoice != null) {
                    Box(
                        modifier = Modifier
                            .size(64.dp)
                            .background(
                                MaterialTheme.colorScheme.primaryContainer,
                                CircleShape
                            )
                            .scale(scale),
                        contentAlignment = Alignment.Center
                    ) {
                        Icon(
                            painter = painterResource(
                                id = when (gameState.userChoice) {
                                    GameChoice.ROCK -> R.drawable.ic_rock
                                    GameChoice.PAPER -> R.drawable.ic_paper
                                    GameChoice.SCISSORS -> R.drawable.ic_scissors
                                }
                            ),
                            contentDescription = gameState.userChoice.getDisplayName(),
                            modifier = Modifier.size(32.dp),
                            tint = MaterialTheme.colorScheme.onPrimaryContainer
                        )
                    }
                } else {
                    Box(
                        modifier = Modifier
                            .size(64.dp)
                            .background(
                                MaterialTheme.colorScheme.surfaceVariant,
                                CircleShape
                            ),
                        contentAlignment = Alignment.Center
                    ) {
                        Text(
                            text = "?",
                            fontSize = 24.sp,
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                    }
                }
            }
            
            // VS text with pulse animation
            val pulseScale by animateFloatAsState(
                targetValue = if (isThinking) 1.1f else 1f,
                animationSpec = infiniteRepeatable(
                    animation = tween(800),
                    repeatMode = RepeatMode.Reverse
                ),
                label = "pulse_scale"
            )
            
            Text(
                text = "VS",
                style = MaterialTheme.typography.titleLarge,
                fontWeight = FontWeight.Bold,
                color = MaterialTheme.colorScheme.primary,
                modifier = Modifier.scale(if (isThinking) pulseScale else 1f)
            )
            
            // Device choice with pet and animations
            Column(
                horizontalAlignment = Alignment.CenterHorizontally
            ) {
                Text(
                    text = "设备",
                    style = MaterialTheme.typography.titleMedium,
                    fontWeight = FontWeight.Medium
                )
                Spacer(modifier = Modifier.height(8.dp))
                
                // Device pet icon with floating and thinking animations
                val floatingOffset by animateFloatAsState(
                    targetValue = if (isThinking) -4f else 0f,
                    animationSpec = infiniteRepeatable(
                        animation = tween(1000),
                        repeatMode = RepeatMode.Reverse
                    ),
                    label = "floating_offset"
                )
                
                val rotationAngle by animateFloatAsState(
                    targetValue = if (isThinking) 360f else 0f,
                    animationSpec = infiniteRepeatable(
                        animation = tween(2000, easing = LinearEasing)
                    ),
                    label = "thinking_rotation"
                )
                
                Box(
                    modifier = Modifier.size(80.dp),
                    contentAlignment = Alignment.Center
                ) {
                    Text(
                        text = petType.getEmoji(),
                        fontSize = 48.sp,
                        modifier = Modifier
                            .offset(y = if (isThinking) floatingOffset.dp else 0.dp)
                            .rotate(if (isThinking) rotationAngle else 0f)
                    )
                    
                    // Device choice overlay with fade animation
                    if (gameState.deviceChoice != null) {
                        Box(
                            modifier = Modifier
                                .size(32.dp)
                                .offset(x = 20.dp, y = (-20).dp)
                                .background(
                                    MaterialTheme.colorScheme.surface,
                                    CircleShape
                                )
                                .alpha(resultAlpha),
                            contentAlignment = Alignment.Center
                        ) {
                            Icon(
                                painter = painterResource(
                                    id = when (gameState.deviceChoice) {
                                        GameChoice.ROCK -> R.drawable.ic_rock
                                        GameChoice.PAPER -> R.drawable.ic_paper
                                        GameChoice.SCISSORS -> R.drawable.ic_scissors
                                    }
                                ),
                                contentDescription = gameState.deviceChoice.getDisplayName(),
                                modifier = Modifier.size(16.dp),
                                tint = MaterialTheme.colorScheme.onSurface
                            )
                        }
                    }
                }
            }
        }
        
        // Score display with fade animation
        if (gameState.userScore > 0 || gameState.deviceScore > 0) {
            Spacer(modifier = Modifier.height(16.dp))
            Text(
                text = "比分: ${gameState.userScore} - ${gameState.deviceScore}",
                style = MaterialTheme.typography.titleMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                modifier = Modifier.alpha(resultAlpha)
            )
        }
    }
}



/**
 * Game choice buttons for user input
 */
@Composable
fun GameChoiceButtons(
    onChoiceSelected: (GameChoice) -> Unit,
    isEnabled: Boolean = true,
    modifier: Modifier = Modifier
) {
    val animationManager = remember { AnimationManager() }
    var selectedChoice by remember { mutableStateOf<GameChoice?>(null) }
    
    Row(
        modifier = modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.SpaceEvenly
    ) {
        GameChoice.values().forEach { choice ->
            val isSelected = selectedChoice == choice
            val scale = animationManager.createBounceAnimation(isSelected)
            
            Button(
                onClick = { 
                    selectedChoice = choice
                    onChoiceSelected(choice)
                },
                enabled = isEnabled,
                modifier = Modifier
                    .size(80.dp)
                    .padding(4.dp)
                    .scale(scale),
                shape = CircleShape,
                colors = ButtonDefaults.buttonColors(
                    containerColor = if (isSelected) 
                        MaterialTheme.colorScheme.secondary 
                    else MaterialTheme.colorScheme.primary
                )
            ) {
                Icon(
                    painter = painterResource(
                        id = when (choice) {
                            GameChoice.ROCK -> R.drawable.ic_rock
                            GameChoice.PAPER -> R.drawable.ic_paper
                            GameChoice.SCISSORS -> R.drawable.ic_scissors
                        }
                    ),
                    contentDescription = choice.getDisplayName(),
                    modifier = Modifier.size(40.dp),
                    tint = Color.White
                )
            }
        }
    }
    
    // Reset selection after animation
    LaunchedEffect(selectedChoice) {
        if (selectedChoice != null) {
            kotlinx.coroutines.delay(300)
            selectedChoice = null
        }
    }
}

@Composable
fun GameChoiceButton(
    choice: GameChoice,
    onClick: () -> Unit,
    enabled: Boolean = true,
    modifier: Modifier = Modifier
) {
    var isPressed by remember { mutableStateOf(false) }
    val scale by animateFloatAsState(
        targetValue = if (isPressed) 0.95f else 1f,
        animationSpec = tween(100),
        label = "button_scale"
    )
    
    Card(
        onClick = onClick,
        enabled = enabled,
        modifier = modifier
            .size(100.dp)
            .scale(scale)
            .pointerInput(Unit) {
                detectTapGestures(
                    onPress = {
                        isPressed = true
                        tryAwaitRelease()
                        isPressed = false
                    }
                )
            },
        shape = CircleShape,
        colors = CardDefaults.cardColors(
            containerColor = if (enabled) {
                MaterialTheme.colorScheme.primaryContainer
            } else {
                MaterialTheme.colorScheme.surfaceVariant
            }
        ),
        elevation = CardDefaults.cardElevation(
            defaultElevation = if (enabled) 8.dp else 2.dp
        )
    ) {
        Column(
            modifier = Modifier.fillMaxSize(),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.Center
        ) {
            Text(
                text = choice.getEmoji(),
                fontSize = 24.sp,
                modifier = Modifier.scale(scale)
            )
            
            Spacer(modifier = Modifier.height(4.dp))
            
            Text(
                text = choice.getDisplayName(),
                style = MaterialTheme.typography.bodySmall,
                color = if (enabled) {
                    MaterialTheme.colorScheme.onPrimaryContainer
                } else {
                    MaterialTheme.colorScheme.onSurfaceVariant
                },
                textAlign = TextAlign.Center
            )
        }
    }
    
    LaunchedEffect(isPressed) {
        if (isPressed) {
            kotlinx.coroutines.delay(100)
            isPressed = false
        }
    }
}

/**
 * Game status text
 */
@Composable
fun GameStatusText(
    animationState: AnimationState,
    isLoading: Boolean,
    modifier: Modifier = Modifier
) {
    val statusText = when {
        isLoading -> "正在处理..."
        animationState == AnimationState.IDLE -> "请选择你的出招"
        animationState == AnimationState.USER_SELECTING -> "你选择了..."
        animationState == AnimationState.DEVICE_THINKING -> "设备正在选择..."
        animationState == AnimationState.SHOWING_RESULT -> "结果出来了！"
        else -> "准备开始游戏"
    }
    
    Text(
        text = statusText,
        style = MaterialTheme.typography.titleMedium,
        color = MaterialTheme.colorScheme.onSurface,
        textAlign = TextAlign.Center,
        modifier = modifier.fillMaxWidth()
    )
}

/**
 * Recent games summary
 */
@Composable
fun RecentGamesSummary(
    recentGames: List<GameRecord>,
    onViewAllGames: () -> Unit,
    modifier: Modifier = Modifier
) {
    Card(
        modifier = modifier.fillMaxWidth(),
        shape = RoundedCornerShape(12.dp),
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.colorScheme.surfaceVariant
        )
    ) {
        Column(
            modifier = Modifier.padding(16.dp)
        ) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = "最近游戏",
                    style = MaterialTheme.typography.titleMedium,
                    fontWeight = FontWeight.Bold,
                    color = MaterialTheme.colorScheme.primary
                )
                
                if (recentGames.isNotEmpty()) {
                    TextButton(onClick = onViewAllGames) {
                        Text("查看全部")
                    }
                }
            }
            
            if (recentGames.isEmpty()) {
                Text(
                    text = "暂无游戏记录",
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                    textAlign = TextAlign.Center,
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(vertical = 8.dp)
                )
            } else {
                recentGames.take(3).forEach { record ->
                    RecentGameItem(record = record)
                }
            }
        }
    }
}

@Composable
fun RecentGameItem(
    record: GameRecord,
    modifier: Modifier = Modifier
) {
    Row(
        modifier = modifier
            .fillMaxWidth()
            .padding(vertical = 4.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        Text(
            text = record.userChoice.getEmoji(),
            fontSize = 20.sp,
            modifier = Modifier.padding(end = 4.dp)
        )
        
        Text(
            text = "vs",
            style = MaterialTheme.typography.bodySmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
            modifier = Modifier.padding(horizontal = 4.dp)
        )
        
        Text(
            text = record.deviceChoice.getEmoji(),
            fontSize = 20.sp,
            modifier = Modifier.padding(start = 4.dp, end = 8.dp)
        )
        
        Text(
            text = record.result.getEmoji(),
            fontSize = 16.sp,
            modifier = Modifier.padding(end = 8.dp)
        )
        
        Spacer(modifier = Modifier.weight(1f))
        
        Text(
            text = record.getFormattedTime(),
            style = MaterialTheme.typography.bodySmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant
        )
    }
}