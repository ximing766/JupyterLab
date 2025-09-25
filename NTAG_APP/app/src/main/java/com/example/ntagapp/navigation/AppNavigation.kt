package com.example.ntagapp.navigation

import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.navigation.NavHostController
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import com.example.ntagapp.ui.screens.GameScreen
import com.example.ntagapp.ui.screens.SettingsScreen
import com.example.ntagapp.ui.screens.StatisticsScreen
import com.example.ntagapp.viewmodel.GameViewModel
import com.example.ntagapp.viewmodel.SettingsViewModel
import com.example.ntagapp.viewmodel.StatisticsViewModel

/**
 * Main navigation component for the app
 */
@Composable
fun AppNavigation(
    navController: NavHostController,
    gameViewModel: GameViewModel,
    settingsViewModel: SettingsViewModel,
    statisticsViewModel: StatisticsViewModel,
    modifier: Modifier = Modifier
) {
    NavHost(
        navController = navController,
        startDestination = Screen.Game.route,
        modifier = modifier
    ) {
        composable(Screen.Game.route) {
            GameScreen(
                gameViewModel = gameViewModel,
                settingsViewModel = settingsViewModel
            )
        }
        
        composable(Screen.Statistics.route) {
            StatisticsScreen(
                viewModel = statisticsViewModel
            )
        }
        
        composable(Screen.Settings.route) {
            SettingsScreen(
                viewModel = settingsViewModel
            )
        }
    }
}