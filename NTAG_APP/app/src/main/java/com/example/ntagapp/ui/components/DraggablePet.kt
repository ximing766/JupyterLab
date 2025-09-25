package com.example.ntagapp.ui.components

import androidx.compose.foundation.gestures.detectDragGestures
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.shadow
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.platform.LocalConfiguration
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.IntOffset
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.ntagapp.model.PetType
import kotlin.math.roundToInt

/**
 * Draggable pet character component
 */
@Composable
fun DraggablePet(
    petType: PetType,
    isVisible: Boolean = true,
    modifier: Modifier = Modifier,
    onPetClicked: () -> Unit = {}
) {
    val configuration = LocalConfiguration.current
    val density = LocalDensity.current
    
    // Screen dimensions
    val screenWidth = with(density) { configuration.screenWidthDp.dp.toPx() }
    val screenHeight = with(density) { configuration.screenHeightDp.dp.toPx() }
    
    // Pet position state
    var offsetX by remember { mutableFloatStateOf(screenWidth * 0.8f) }
    var offsetY by remember { mutableFloatStateOf(screenHeight * 0.3f) }
    
    if (isVisible) {
        Box(
            modifier = modifier
                .offset { IntOffset(offsetX.roundToInt(), offsetY.roundToInt()) }
                .size(80.dp)
                .pointerInput(Unit) {
                    detectDragGestures { change, _ ->
                        val newX = (offsetX + change.position.x).coerceIn(0f, screenWidth - 80.dp.toPx())
                        val newY = (offsetY + change.position.y).coerceIn(0f, screenHeight - 80.dp.toPx())
                        offsetX = newX
                        offsetY = newY
                    }
                }
        ) {
            // Pet character
            Card(
                modifier = Modifier
                    .fillMaxSize()
                    .shadow(4.dp, CircleShape),
                shape = CircleShape,
                colors = CardDefaults.cardColors(
                    containerColor = MaterialTheme.colorScheme.primaryContainer
                ),
                onClick = onPetClicked
            ) {
                Box(
                    modifier = Modifier.fillMaxSize(),
                    contentAlignment = Alignment.Center
                ) {
                    Text(
                        text = petType.getEmoji(),
                        fontSize = 32.sp,
                        fontWeight = FontWeight.Bold
                    )
                }
            }
        }
    }
}