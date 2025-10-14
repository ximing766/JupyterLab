package com.example.uwbota

import android.Manifest
import android.app.Activity
import android.bluetooth.BluetoothAdapter
import android.bluetooth.BluetoothManager
import android.content.Intent
import android.content.pm.PackageManager
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.os.Environment
import android.widget.Toast
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat
import androidx.core.view.WindowCompat
import androidx.core.view.WindowInsetsCompat
import androidx.core.view.WindowInsetsControllerCompat
import androidx.lifecycle.ViewModelProvider
import com.example.uwbota.databinding.ActivityMainBinding
import com.example.uwbota.ble.BleManager
import com.example.uwbota.OtaManager
import com.example.uwbota.FirmwareType
import com.example.uwbota.ui.DeviceSelectionDialog
import com.example.uwbota.utils.LogManager
import java.io.File
import java.io.FileWriter
import java.io.InputStream
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

class MainActivity : AppCompatActivity() {
    private lateinit var binding: ActivityMainBinding
    private lateinit var bleManager: BleManager
    private lateinit var otaManager: OtaManager
    private var selectedFirmwareUri: Uri? = null
    private var selectedFirmwareData: ByteArray? = null
    
    private val bluetoothAdapter: BluetoothAdapter? by lazy {
        val bluetoothManager = getSystemService(BLUETOOTH_SERVICE) as BluetoothManager
        bluetoothManager.adapter
    }
    
    // File picker launcher
    private val filePickerLauncher = registerForActivityResult(
        ActivityResultContracts.GetContent()
    ) { uri: Uri? ->
        uri?.let {
            selectedFirmwareUri = it
            loadFirmwareFile(it)
        }
    }
    
    // Bluetooth enable launcher
    private val enableBluetoothLauncher = registerForActivityResult(
        ActivityResultContracts.StartActivityForResult()
    ) { result ->
        if (result.resultCode == Activity.RESULT_OK) {
            logMessage("Bluetooth enabled")
        } else {
            logMessage("Bluetooth not enabled")
            Toast.makeText(this, "Bluetooth is required for OTA update", Toast.LENGTH_LONG).show()
        }
    }
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        
        // Enable edge-to-edge display for modern look
        WindowCompat.setDecorFitsSystemWindows(window, false)
        
        binding = ActivityMainBinding.inflate(layoutInflater)
        setContentView(binding.root)
        
        // Setup window insets for edge-to-edge
        setupEdgeToEdge()
        
        initializeComponents()
        setupClickListeners()
        checkPermissions()
    }
    
    private fun setupEdgeToEdge() {
        // Handle window insets for edge-to-edge display
        binding.root.setOnApplyWindowInsetsListener { view, insets ->
            val systemBars = insets.getInsets(WindowInsetsCompat.Type.systemBars())
            view.setPadding(
                systemBars.left,
                systemBars.top,
                systemBars.right,
                systemBars.bottom
            )
            insets
        }
    }
    
    private fun initializeComponents() {
        LogManager.setUiLogCallback { message ->
            runOnUiThread {
                logMessage(message)
            }
        }
        
        bleManager = BleManager(this)
        otaManager = OtaManager(this, bleManager)
        
        // Setup BLE manager callbacks
        bleManager.onConnectionStateChanged = { isConnected, error ->
            runOnUiThread {
                updateConnectionStatus(isConnected)
                error?.let { logMessage("Connection error: $it") }
            }
        }
        
        bleManager.onDataReceived = { data ->
            runOnUiThread {
                otaManager.handleReceivedData(data)
            }
        }
        
        otaManager.onProgressUpdate = { progress, total, message, speed, transferred, totalBytes ->
            runOnUiThread {
                updateProgress(progress, speed, transferred, totalBytes)
                message?.let { logMessage(it) }
            }
        }
        
        otaManager.onStatusUpdate = { status ->
            status?.let {
                runOnUiThread {
                    updateOtaStatus(it)
                }
            }
        }
        
        otaManager.onOtaComplete = { success, message ->
            runOnUiThread {
                if (success) {
                    updateOtaStatus("Update completed successfully")
                } else {
                    updateOtaStatus("Update failed: $message")
                }
                binding.btnStartUpdate.isEnabled = true
                binding.btnSR150Update.isEnabled = true
                binding.btnSelectFile.isEnabled = true
                binding.btnScanDevices.isEnabled = true
                binding.btnDisconnect.isEnabled = true  // Re-enable disconnect after OTA
            }
        }
    }
    
    private fun setupClickListeners() {
        binding.btnSelectFile.setOnClickListener {
            filePickerLauncher.launch("*/*")
        }
        
        binding.btnScanDevices.setOnClickListener {
            if (checkBluetoothEnabled()) {
                showDeviceSelectionDialog()
            }
        }
        
        binding.btnDisconnect.setOnClickListener {
            bleManager.disconnect()
            // Immediately update UI to show disconnected state
            updateConnectionStatus(false)
        }
        
        binding.btnStartUpdate.setOnClickListener {
            startOtaUpdate()
        }
        
        binding.btnSR150Update.setOnClickListener {
            startSR150Update()
        }
    }
    
    private fun checkPermissions() {
        val permissions = mutableListOf<String>()
        
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            permissions.addAll(listOf(
                Manifest.permission.BLUETOOTH_SCAN,
                Manifest.permission.BLUETOOTH_CONNECT,
                Manifest.permission.ACCESS_FINE_LOCATION
            ))
        } else {
            permissions.addAll(listOf(
                Manifest.permission.BLUETOOTH,
                Manifest.permission.BLUETOOTH_ADMIN,
                Manifest.permission.ACCESS_FINE_LOCATION
            ))
        }
        
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            permissions.add(Manifest.permission.READ_MEDIA_IMAGES)
        } else {
            permissions.add(Manifest.permission.READ_EXTERNAL_STORAGE)
        }
        
        val missingPermissions = permissions.filter {
            ContextCompat.checkSelfPermission(this, it) != PackageManager.PERMISSION_GRANTED
        }
        
        if (missingPermissions.isNotEmpty()) {
            ActivityCompat.requestPermissions(this, missingPermissions.toTypedArray(), 1001)
        }
    }
    
    private fun checkBluetoothEnabled(): Boolean {
        return if (bluetoothAdapter?.isEnabled == true) {
            true
        } else {
            val enableBtIntent = Intent(BluetoothAdapter.ACTION_REQUEST_ENABLE)
            enableBluetoothLauncher.launch(enableBtIntent)
            false
        }
    }
    
    private fun loadFirmwareFile(uri: Uri) {
        try {
            val fileName = getFileName(uri)
            
            // Check if file has .bin extension
            if (!fileName.lowercase().endsWith(".bin")) {
                logMessage("Error: Only .bin files are supported")
                Toast.makeText(this, "Please select .bin file", Toast.LENGTH_SHORT).show()
                return
            }
            
            val inputStream: InputStream? = contentResolver.openInputStream(uri)
            selectedFirmwareData = inputStream?.readBytes()
            inputStream?.close()
            
            binding.tvSelectedFile.text = "Selected: $fileName (${selectedFirmwareData?.size ?: 0} bytes)"
            logMessage("Firmware file loaded: $fileName")
            
            updateStartButtonState()
        } catch (e: Exception) {
            logMessage("Error loading firmware file: ${e.message}")
            Toast.makeText(this, "Error loading firmware file", Toast.LENGTH_SHORT).show()
        }
    }
    
    private fun getFileName(uri: Uri): String {
        var result: String? = null
        if (uri.scheme == "content") {
            val cursor = contentResolver.query(uri, null, null, null, null)
            cursor?.use {
                if (it.moveToFirst()) {
                    val columnIndex = it.getColumnIndex("_display_name")
                    if (columnIndex >= 0) {
                        result = it.getString(columnIndex)
                    }
                }
            }
        }
        if (result == null) {
            result = uri.path
            val cut = result?.lastIndexOf('/')
            if (cut != -1 && cut != null) {
                result = result?.substring(cut + 1)
            }
        }
        return result ?: "unknown_file"
    }
    
    private fun showDeviceSelectionDialog() {
        val dialog = DeviceSelectionDialog(this, bleManager) { deviceAddress ->
            bleManager.connectToDevice(deviceAddress)
        }
        dialog.show()
    }
    
    private fun updateConnectionStatus(isConnected: Boolean) {
        if (isConnected) {
            binding.tvConnectionStatus.text = "Connected to BLE device"
            binding.btnScanDevices.text = "Connected"
            binding.btnScanDevices.isEnabled = false
            binding.btnDisconnect.isEnabled = true
        } else {
            binding.tvConnectionStatus.text = "Not connected"
            binding.btnScanDevices.text = "Scan Devices"
            binding.btnScanDevices.isEnabled = true
            binding.btnDisconnect.isEnabled = false
            LogManager.i("BLE connection lost")
        }
        updateStartButtonState()
    }
    
    private fun updateStartButtonState() {
        val canStart = selectedFirmwareData != null && bleManager.isConnected()
        binding.btnStartUpdate.isEnabled = canStart
        binding.btnSR150Update.isEnabled = canStart
    }
    
    private fun startOtaUpdate() {
        selectedFirmwareData?.let { firmwareData ->
            LogManager.i("Starting OTA update with ${firmwareData.size} bytes")
            binding.btnStartUpdate.isEnabled = false
            binding.btnSR150Update.isEnabled = false
            binding.btnSelectFile.isEnabled = false
            binding.btnScanDevices.isEnabled = false
            binding.btnDisconnect.isEnabled = false  // Disable disconnect during OTA
            
            selectedFirmwareUri?.let { uri ->
                // Default to APP firmware type
                otaManager.startOtaUpgrade(uri, FirmwareType.APP_FIRMWARE)
            }
        }
    }
    
    private fun startSR150Update() {
        selectedFirmwareData?.let { firmwareData ->
            LogManager.i("Starting SR150 OTA update with ${firmwareData.size} bytes")
            binding.btnStartUpdate.isEnabled = false
            binding.btnSR150Update.isEnabled = false
            binding.btnSelectFile.isEnabled = false
            binding.btnScanDevices.isEnabled = false
            binding.btnDisconnect.isEnabled = false  // Disable disconnect during OTA
            
            selectedFirmwareUri?.let { uri ->
                // Use SR150 firmware type
                otaManager.startOtaUpgrade(uri, FirmwareType.SR150_FIRMWARE)
            }
        }
    }
    
    private var startTime: Long = 0
    private var totalBytes: Long = 0
    private var transferredBytes: Long = 0
    
    private fun updateProgress(progress: Int, speed: String? = null, transferred: Long = 0, total: Long = 0) {
        // Update progress bar directly without animation
        binding.progressBar.progress = progress
        
        // Update progress percentage
        binding.tvProgress.text = "$progress%"
        
        // Update transfer speed
        if (speed != null) {
            binding.tvTransferSpeed.text = speed
        } else {
            binding.tvTransferSpeed.text = "0 KB/s"
        }
        
        // Update data transferred info
        if (total > 0) {
            totalBytes = total
            transferredBytes = transferred
            val transferredKB = transferred / 1024
            val totalKB = total / 1024
            binding.tvDataTransferred.text = "$transferredKB / $totalKB KB"
        }
        
        // Calculate and update remaining time
        updateTimeRemaining(progress, speed)
        
        // Update progress bar color based on status
        updateProgressBarColor(progress)
    }
    
    private fun updateTimeRemaining(progress: Int, speed: String?) {
        if (progress > 0 && speed != null && speed.contains("KB/s")) {
            try {
                val speedValue = speed.replace(" KB/s", "").toFloatOrNull()
                if (speedValue != null && speedValue > 0) {
                    val remainingBytes = totalBytes - transferredBytes
                    val remainingSeconds = (remainingBytes / 1024) / speedValue
                    val minutes = (remainingSeconds / 60).toInt()
                    val seconds = (remainingSeconds % 60).toInt()
                    binding.tvTimeRemaining.text = String.format("%02d:%02d", minutes, seconds)
                } else {
                    binding.tvTimeRemaining.text = "--:--"
                }
            } catch (e: Exception) {
                binding.tvTimeRemaining.text = "--:--"
            }
        } else {
            binding.tvTimeRemaining.text = "--:--"
        }
    }
    
    private fun updateProgressBarColor(progress: Int) {
        val progressDrawable = when {
            progress >= 100 -> ContextCompat.getDrawable(this, R.drawable.progress_bar_complete)
            progress > 0 -> ContextCompat.getDrawable(this, R.drawable.custom_progress_bar)
            else -> ContextCompat.getDrawable(this, R.drawable.custom_progress_bar)
        }
        binding.progressBar.progressDrawable = progressDrawable
    }
    
    private fun setProgressBarError() {
        val errorDrawable = ContextCompat.getDrawable(this, R.drawable.progress_bar_error)
        binding.progressBar.progressDrawable = errorDrawable
    }
    
    private fun updateOtaStatus(status: String) {
        binding.tvUpdateStatus.text = status
        
        // Update progress bar color based on status
        if (status.contains("failed", ignoreCase = true) ||
            status.contains("error", ignoreCase = true)) {
            setProgressBarError()
        }
        
        // Re-enable buttons when update is complete or failed
        if (status.contains("completed", ignoreCase = true) || 
            status.contains("failed", ignoreCase = true) ||
            status.contains("error", ignoreCase = true)) {
            binding.btnStartUpdate.isEnabled = true
            binding.btnSR150Update.isEnabled = true
            binding.btnSelectFile.isEnabled = true
            binding.btnScanDevices.isEnabled = !bleManager.isConnected()
        }
    }
    
    private fun logMessage(message: String) {
        val timestamp = java.text.SimpleDateFormat("HH:mm:ss", java.util.Locale.getDefault())
            .format(java.util.Date())
        val logText = "[$timestamp] $message\n"
        binding.tvLog.append(logText)
        
        // Auto-scroll to bottom
        binding.tvLog.post {
            val scrollView = binding.tvLog.parent as? android.widget.ScrollView
            scrollView?.let { sv ->
                val maxScrollY = sv.getChildAt(0).height - sv.height
                sv.smoothScrollTo(0, maxScrollY)
            }
        }
    }
    
    override fun onRequestPermissionsResult(
        requestCode: Int,
        permissions: Array<out String>,
        grantResults: IntArray
    ) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults)
        if (requestCode == 1001) {
            val deniedPermissions = permissions.filterIndexed { index, _ ->
                grantResults[index] != PackageManager.PERMISSION_GRANTED
            }
            
            if (deniedPermissions.isNotEmpty()) {
                Toast.makeText(
                    this,
                    "Some permissions are required for the app to work properly",
                    Toast.LENGTH_LONG
                ).show()
                LogManager.w("Permissions denied: ${deniedPermissions.joinToString(", ")}")
            } else {
                LogManager.i("All permissions granted")
            }
        }
    }
    
    override fun onDestroy() {
        super.onDestroy()
        bleManager.disconnect()
    }
}