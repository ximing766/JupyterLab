package com.example.ntagapp.ui.screens

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Delete
import androidx.compose.material.icons.filled.TrendingUp
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.example.ntagapp.model.GameStatistics
import com.example.ntagapp.viewmodel.StatisticsViewModel

/**
 * Statistics screen
 */
@Composable
fun StatisticsScreen(
    viewModel: StatisticsViewModel,
    modifier: Modifier = Modifier
) {
    val statistics by viewModel.statistics.collectAsStateWithLifecycle()
    
    LaunchedEffect(Unit) {
        viewModel.loadStatistics()
    }
    
    Column(
        modifier = modifier
            .fillMaxSize()
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp)
    ) {
        // Title and Actions
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text(
                text = "统计数据",
                style = MaterialTheme.typography.headlineMedium,
                fontWeight = FontWeight.Bold
            )
            
            IconButton(
                onClick = { viewModel.clearAllData() }
            ) {
                Icon(
                    imageVector = Icons.Default.Delete,
                    contentDescription = "清除数据",
                    tint = MaterialTheme.colorScheme.error
                )
            }
        }
        
        // Basic Statistics
        StatisticsOverviewCard(statistics = statistics)
    }
}

@Composable
fun StatisticsOverviewCard(
    statistics: GameStatistics,
    modifier: Modifier = Modifier
) {
    Card(
        modifier = modifier.fillMaxWidth(),
        shape = RoundedCornerShape(12.dp),
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.colorScheme.primaryContainer
        )
    ) {
        Column(
            modifier = Modifier.padding(16.dp)
        ) {
            Row(
                verticalAlignment = Alignment.CenterVertically,
                modifier = Modifier.padding(bottom = 12.dp)
            ) {
                Icon(
                    imageVector = Icons.Default.TrendingUp,
                    contentDescription = null,
                    tint = MaterialTheme.colorScheme.primary,
                    modifier = Modifier.padding(end = 8.dp)
                )
                Text(
                    text = "游戏统计",
                    style = MaterialTheme.typography.titleLarge,
                    fontWeight = FontWeight.Bold,
                    color = MaterialTheme.colorScheme.primary
                )
            }
            
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceEvenly
            ) {
                StatisticItem(
                    label = "总场次",
                    value = statistics.totalGames.toString(),
                    color = MaterialTheme.colorScheme.onPrimaryContainer
                )
                StatisticItem(
                    label = "胜率",
                    value = "${if (statistics.totalGames > 0) (statistics.wins * 100 / statistics.totalGames) else 0}%",
                    color = Color(0xFF4CAF50)
                )
            }
            
            Spacer(modifier = Modifier.height(12.dp))
            
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceEvenly
            ) {
                StatisticItem(
                    label = "胜场",
                    value = statistics.wins.toString(),
                    color = Color(0xFF4CAF50)
                )
                StatisticItem(
                    label = "负场",
                    value = statistics.losses.toString(),
                    color = Color(0xFFF44336)
                )
                StatisticItem(
                    label = "平局",
                    value = statistics.draws.toString(),
                    color = Color(0xFF9E9E9E)
                )
            }
        }
    }
}



@Composable
fun StatisticItem(
    label: String,
    value: String,
    color: Color,
    modifier: Modifier = Modifier
) {
    Column(
        horizontalAlignment = Alignment.CenterHorizontally,
        modifier = modifier
    ) {
        Text(
            text = value,
            style = MaterialTheme.typography.headlineMedium,
            fontWeight = FontWeight.Bold,
            color = color
        )
        Text(
            text = label,
            style = MaterialTheme.typography.bodySmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant
        )
    }
}