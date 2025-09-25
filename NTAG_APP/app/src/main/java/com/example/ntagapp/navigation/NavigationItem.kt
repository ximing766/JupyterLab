package com.example.ntagapp.navigation

import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Games
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material.icons.filled.BarChart
import androidx.compose.ui.graphics.vector.ImageVector

/**
 * Sealed class representing navigation destinations
 */
sealed class Screen(val route: String) {
    object Game : Screen("game")
    object Statistics : Screen("statistics")
    object Settings : Screen("settings")
}

/**
 * Data class for bottom navigation items
 */
data class NavigationItem(
    val screen: Screen,
    val title: String,
    val icon: ImageVector,
    val description: String
)

/**
 * List of bottom navigation items
 */
val bottomNavigationItems = listOf(
    NavigationItem(
        screen = Screen.Game,
        title = "游戏",
        icon = Icons.Default.Games,
        description = "剪刀石头布游戏"
    ),
    NavigationItem(
        screen = Screen.Statistics,
        title = "统计",
        icon = Icons.Default.BarChart,
        description = "游戏统计数据"
    ),
    NavigationItem(
        screen = Screen.Settings,
        title = "设置",
        icon = Icons.Default.Settings,
        description = "应用设置"
    )
)