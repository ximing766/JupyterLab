package com.example.ntagapp

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Scaffold
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.navigation.compose.rememberNavController
import com.example.ntagapp.audio.AudioManager
import com.example.ntagapp.data.database.GameDatabase
import com.example.ntagapp.navigation.AppNavigation
import com.example.ntagapp.repository.GameRepository
import com.example.ntagapp.repository.SettingsRepository
import com.example.ntagapp.ui.components.BottomNavigationBar
import com.example.ntagapp.ui.theme.NTAGAPPTheme
import com.example.ntagapp.viewmodel.GameViewModel
import com.example.ntagapp.viewmodel.GameViewModelFactory
import com.example.ntagapp.viewmodel.SettingsViewModel
import com.example.ntagapp.viewmodel.SettingsViewModelFactory
import com.example.ntagapp.viewmodel.StatisticsViewModel
import com.example.ntagapp.viewmodel.StatisticsViewModelFactory

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            NTAGAPPTheme {
                RockPaperScissorsApp()
            }
        }
    }
}

@Composable
fun RockPaperScissorsApp() {
    val navController = rememberNavController()
    val context = androidx.compose.ui.platform.LocalContext.current
    
    // Initialize repositories and managers
    val database = GameDatabase.getDatabase(context)
    val gameRepository = GameRepository(database.gameRecordDao())
    val settingsRepository = SettingsRepository(context)
    val audioManager = AudioManager(context)
    
    // Initialize ViewModels
    val gameViewModel: GameViewModel = viewModel(
        factory = GameViewModelFactory(gameRepository, audioManager)
    )
    val settingsViewModel: SettingsViewModel = viewModel(
        factory = SettingsViewModelFactory(settingsRepository)
    )
    val statisticsViewModel: StatisticsViewModel = viewModel(
        factory = StatisticsViewModelFactory(gameRepository)
    )
    
    Scaffold(
        modifier = Modifier.fillMaxSize(),
        bottomBar = {
            BottomNavigationBar(
                navController = navController
            )
        }
    ) { innerPadding ->
        AppNavigation(
            navController = navController,
            gameViewModel = gameViewModel,
            settingsViewModel = settingsViewModel,
            statisticsViewModel = statisticsViewModel,
            modifier = Modifier.padding(innerPadding)
        )
    }
}