package com.example.ntagapp.ui.screens

import androidx.compose.foundation.layout.*
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.example.ntagapp.ui.components.*
import com.example.ntagapp.ui.components.DraggablePet
import com.example.ntagapp.viewmodel.GameViewModel
import com.example.ntagapp.viewmodel.SettingsViewModel

/**
 * Game screen
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun GameScreen(
    gameViewModel: GameViewModel,
    settingsViewModel: SettingsViewModel,
    modifier: Modifier = Modifier
) {
    val gameState by gameViewModel.gameState.collectAsStateWithLifecycle()
    val settings by settingsViewModel.settings.collectAsStateWithLifecycle()
    
    Box(
        modifier = modifier.fillMaxSize()
    ) {
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(16.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.Center
        ) {
            // Title
            Text(
                text = "剪刀石头布",
                style = MaterialTheme.typography.headlineLarge,
                fontWeight = FontWeight.Bold,
                color = MaterialTheme.colorScheme.primary,
                modifier = Modifier.padding(bottom = 32.dp)
            )
            
            // Current Score
            Text(
                text = "得分: ${gameState.score}",
                style = MaterialTheme.typography.headlineSmall,
                modifier = Modifier.padding(bottom = 24.dp)
            )
            
            // Game Result Display
            GameResultDisplay(
                gameState = gameState,
                petType = settings.selectedPetType,
                modifier = Modifier.padding(horizontal = 16.dp)
            )
            
            Spacer(modifier = Modifier.height(32.dp))
            
            // Game Status Text
            GameStatusText(
                animationState = gameState.animationState,
                isLoading = gameState.isLoading
            )
            
            Spacer(modifier = Modifier.height(32.dp))
            
            // Game Choice Buttons
            GameChoiceButtons(
                onChoiceSelected = { choice ->
                    gameViewModel.playGame(choice)
                },
                isEnabled = !gameState.isLoading
            )
            
            Spacer(modifier = Modifier.height(32.dp))
            
            // Reset Button
            OutlinedButton(
                onClick = { gameViewModel.resetScore() }
            ) {
                Icon(
                    imageVector = Icons.Default.Refresh,
                    contentDescription = null,
                    modifier = Modifier.padding(end = 8.dp)
                )
                Text("重置分数")
            }
        }
        
        // Draggable Pet
        DraggablePet(
            petType = settings.selectedPetType,
            isVisible = true,
            onPetClicked = {
                // Pet interaction - could play sound or show animation
            }
        )
    }
}