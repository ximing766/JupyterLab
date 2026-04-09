package com.example.uwbota

import android.app.Activity
import android.bluetooth.BluetoothAdapter
import android.bluetooth.BluetoothManager
import android.content.Context
import android.content.Intent
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.os.Environment
import android.provider.DocumentsContract
import android.provider.Settings
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.Toast
import androidx.activity.result.contract.ActivityResultContracts
import androidx.core.content.ContextCompat
import androidx.fragment.app.Fragment
import com.example.uwbota.ble.BleManager
import com.example.uwbota.databinding.FragmentHomeBinding
import com.example.uwbota.ui.DeviceSelectionDialog
import com.example.uwbota.FirmwareType
import com.example.uwbota.utils.LogManager
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import org.json.JSONArray
import java.io.File
import java.io.FileOutputStream
import java.io.InputStream
import java.net.HttpURLConnection
import java.net.URL
import java.text.SimpleDateFormat
import java.util.Locale

class HomeFragment : Fragment() {
    private var _binding: FragmentHomeBinding? = null
    private val binding get() = _binding!!
    
    // Get BleManager from MainActivity
    private val bleManager get() = (requireActivity() as MainActivity).bleManager
    private lateinit var otaManager: OtaManager
    
    private var selectedFirmwareUri: Uri? = null
    private var selectedFirmwareData: ByteArray? = null
    
    private var startTime: Long = 0
    private var totalBytes: Long = 0
    private var transferredBytes: Long = 0

    // File picker launcher
    private val filePickerLauncher = registerForActivityResult(
        ActivityResultContracts.StartActivityForResult()
    ) { result ->
        if (result.resultCode == Activity.RESULT_OK) {
            result.data?.data?.let { uri ->
                selectedFirmwareUri = uri
                loadFirmwareFile(uri)
            }
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
            Toast.makeText(context, "Bluetooth is required for OTA update", Toast.LENGTH_LONG).show()
        }
    }

    override fun onCreateView(
        inflater: LayoutInflater,
        container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View {
        _binding = FragmentHomeBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        
        initializeComponents()
        setupClickListeners()
        
        // Initial UI state update
        updateConnectionStatus(bleManager.isConnected())

        // Auto sync on start
        if (checkStoragePermission()) {
            syncFirmwareFromGitee()
        }
    }
    
    private fun initializeComponents() {
        LogManager.setUiLogCallback { message ->
            activity?.runOnUiThread {
                logMessage(message)
            }
        }
        
        otaManager = OtaManager(requireContext(), bleManager)
        
        // Setup BLE manager callbacks
        bleManager.onConnectionStateChanged = { isConnected, error ->
            activity?.runOnUiThread {
                updateConnectionStatus(isConnected)
                error?.let { logMessage("Connection error: $it") }
            }
        }
        
        bleManager.onDataReceived = { data ->
            activity?.runOnUiThread {
                otaManager.handleReceivedData(data)
            }
        }
        
        otaManager.onProgressUpdate = { progress, total, message, speed, transferred, totalBytes ->
            activity?.runOnUiThread {
                updateProgress(progress, speed, transferred, totalBytes)
                message?.let { logMessage(it) }
            }
        }
        
        otaManager.onStatusUpdate = { status ->
            status?.let {
                activity?.runOnUiThread {
                    updateOtaStatus(it)
                }
            }
        }
        
        otaManager.onOtaComplete = { success, message ->
            activity?.runOnUiThread {
                if (success) {
                    updateOtaStatus("Update completed successfully")
                } else {
                    updateOtaStatus("Update failed: $message")
                }
                binding.btnStartUpdate.isEnabled = true
                binding.btnSR150Update.isEnabled = true
                binding.btnSelectFile.isEnabled = true
                binding.btnScanDevices.isEnabled = true
                binding.btnDisconnect.isEnabled = true
            }
        }
    }
    
    private fun setupClickListeners() {
        binding.btnSelectFile.setOnClickListener {
            openFilePicker()
        }

        binding.btnSyncGitee.setOnClickListener {
            if (checkStoragePermission()) {
                syncFirmwareFromGitee()
            }
        }
        
        binding.btnScanDevices.setOnClickListener {
            if (checkBluetoothEnabled()) {
                showDeviceSelectionDialog()
            }
        }
        
        binding.btnDisconnect.setOnClickListener {
            bleManager.disconnect()
            updateConnectionStatus(false)
        }
        
        binding.btnStartUpdate.setOnClickListener {
            startOtaUpdate()
        }
        
        binding.btnSR150Update.setOnClickListener {
            startSR150Update()
        }
    }
    
    private fun checkStoragePermission(): Boolean {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
            if (!Environment.isExternalStorageManager()) {
                try {
                    val intent = Intent(Settings.ACTION_MANAGE_APP_ALL_FILES_ACCESS_PERMISSION)
                    intent.addCategory("android.intent.category.DEFAULT")
                    intent.data = Uri.parse("package:${requireContext().packageName}")
                    startActivity(intent)
                    Toast.makeText(context, "Please grant all files access permission to sync firmware", Toast.LENGTH_LONG).show()
                } catch (e: Exception) {
                    val intent = Intent()
                    intent.action = Settings.ACTION_MANAGE_ALL_FILES_ACCESS_PERMISSION
                    startActivity(intent)
                }
                return false
            }
        }
        return true
    }

    private fun syncFirmwareFromGitee() {
        logMessage("Starting firmware sync...")
        binding.btnSyncGitee.isEnabled = false
        
        CoroutineScope(Dispatchers.IO).launch {
            try {
                val repoOwner = "ximing766"
                val repoName = "utn3.2_firmware"
                val targetDir = File(Environment.getExternalStorageDirectory(), "UWB")
                
                if (!targetDir.exists()) {
                    if (targetDir.mkdirs()) {
                        withContext(Dispatchers.Main) { logMessage("Created directory: ${targetDir.absolutePath}") }
                    } else {
                         withContext(Dispatchers.Main) { logMessage("Failed to create directory: ${targetDir.absolutePath}") }
                         return@launch
                    }
                } else {
                    // Clean up old IN* or OUT* bin files
                    var deletedCount = 0
                    targetDir.listFiles()?.forEach { file ->
                        if (file.isFile && file.name.lowercase().endsWith(".bin") &&
                            (file.name.uppercase().startsWith("IN") || file.name.uppercase().startsWith("OUT"))) {
                            if (file.delete()) {
                                deletedCount++
                                LogManager.i("Deleted old firmware file: ${file.name}")
                            }
                        }
                    }
                    if (deletedCount > 0) {
                        withContext(Dispatchers.Main) { logMessage("Cleaned up $deletedCount old firmware files") }
                    }
                }

                val apiUrl = "https://gitee.com/api/v5/repos/$repoOwner/$repoName/contents/bin?ref=main"
                // withContext(Dispatchers.Main) { logMessage("Fetching file list from Gitee...") }
                
                val url = URL(apiUrl)
                val connection = url.openConnection() as HttpURLConnection
                connection.requestMethod = "GET"
                connection.connectTimeout = 10000
                connection.readTimeout = 10000
                
                val jsonString = connection.inputStream.bufferedReader().use { it.readText() }
                val jsonArray = JSONArray(jsonString)
                
                var downloadCount = 0
                
                for (i in 0 until jsonArray.length()) {
                    val item = jsonArray.getJSONObject(i)
                    val name = item.getString("name")
                    val type = item.getString("type")
                    val downloadUrl = item.getString("download_url")
                    
                    if (type == "file" && name.endsWith(".bin", ignoreCase = true)) {
                        val file = File(targetDir, name)
                        val isUpdate = file.exists()
                        
                        withContext(Dispatchers.Main) { 
                            if (isUpdate) {
                                logMessage("Updating: $name")
                            } else {
                                logMessage("Downloading: $name")
                            }
                        }
                        
                        downloadFile(downloadUrl, file)
                        downloadCount++
                        // withContext(Dispatchers.Main) { logMessage("Successfully saved: ${file.name}") }
                    }
                }
                
                withContext(Dispatchers.Main) { 
                    logMessage("Sync complete. $downloadCount files.") 
                    Toast.makeText(context, "Sync complete", Toast.LENGTH_SHORT).show()
                }
            } catch (e: Exception) {
                e.printStackTrace()
                withContext(Dispatchers.Main) { 
                    logMessage("Sync failed: ${e.message}")
                    Toast.makeText(context, "Sync failed: ${e.message}", Toast.LENGTH_LONG).show()
                }
            } finally {
                withContext(Dispatchers.Main) { binding.btnSyncGitee.isEnabled = true }
            }
        }
    }

    private fun downloadFile(urlStr: String, outputFile: File) {
        val url = URL(urlStr)
        val connection = url.openConnection() as HttpURLConnection
        connection.requestMethod = "GET"
        connection.connectTimeout = 10000
        connection.readTimeout = 10000
        connection.connect()
        
        connection.inputStream.use { input ->
            FileOutputStream(outputFile).use { output ->
                input.copyTo(output)
            }
        }
    }

    private fun openFilePicker() {
        val intent = Intent(Intent.ACTION_OPEN_DOCUMENT).apply {
            addCategory(Intent.CATEGORY_OPENABLE)
            type = "*/*" 
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                val uri = Uri.parse("content://com.android.externalstorage.documents/document/primary%3AUWB%2F")
                putExtra(DocumentsContract.EXTRA_INITIAL_URI, uri)
            }
        }
        try {
            filePickerLauncher.launch(intent)
        } catch (e: Exception) {
            // Fallback if system doesn't support the intent
            val fallbackIntent = Intent(Intent.ACTION_GET_CONTENT).apply {
                type = "*/*"
            }
            filePickerLauncher.launch(fallbackIntent)
        }
    }

    private fun checkBluetoothEnabled(): Boolean {
        val bluetoothManager = requireContext().getSystemService(Context.BLUETOOTH_SERVICE) as BluetoothManager
        val adapter = bluetoothManager.adapter
        
        return if (adapter?.isEnabled == true) {
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
            
            if (!fileName.lowercase().endsWith(".bin")) {
                logMessage("Error: Only .bin files are supported")
                Toast.makeText(context, "Please select .bin file", Toast.LENGTH_SHORT).show()
                return
            }
            
            val inputStream: InputStream? = requireContext().contentResolver.openInputStream(uri)
            selectedFirmwareData = inputStream?.readBytes()
            inputStream?.close()
            
            binding.tvSelectedFile.text = "Selected: $fileName (${selectedFirmwareData?.size ?: 0} bytes)"
            // logMessage("Firmware file loaded: $fileName")
            
            updateStartButtonState()
        } catch (e: Exception) {
            logMessage("Error loading firmware file: ${e.message}")
            Toast.makeText(context, "Error loading firmware file", Toast.LENGTH_SHORT).show()
        }
    }
    
    private fun getFileName(uri: Uri): String {
        var result: String? = null
        if (uri.scheme == "content") {
            val cursor = requireContext().contentResolver.query(uri, null, null, null, null)
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
        val dialog = DeviceSelectionDialog(requireContext(), bleManager) { deviceAddress ->
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
            binding.btnDisconnect.isEnabled = false
            
            selectedFirmwareUri?.let { uri ->
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
            binding.btnDisconnect.isEnabled = false
            
            selectedFirmwareUri?.let { uri ->
                otaManager.startOtaUpgrade(uri, FirmwareType.SR150_FIRMWARE)
            }
        }
    }
    
    private fun updateProgress(progress: Int, speed: String? = null, transferred: Long = 0, total: Long = 0) {
        binding.progressBar.progress = progress
        binding.tvProgress.text = "$progress%"
        
        if (speed != null) {
            binding.tvTransferSpeed.text = speed
        } else {
            binding.tvTransferSpeed.text = "0 KB/s"
        }
        
        if (total > 0) {
            totalBytes = total
            transferredBytes = transferred
            val transferredKB = transferred / 1024
            val totalKB = total / 1024
            binding.tvDataTransferred.text = "$transferredKB / $totalKB KB"
        }
        
        updateTimeRemaining(progress, speed)
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
            progress >= 100 -> ContextCompat.getDrawable(requireContext(), R.drawable.progress_bar_complete)
            progress > 0 -> ContextCompat.getDrawable(requireContext(), R.drawable.custom_progress_bar)
            else -> ContextCompat.getDrawable(requireContext(), R.drawable.custom_progress_bar)
        }
        binding.progressBar.progressDrawable = progressDrawable
    }
    
    private fun setProgressBarError() {
        val errorDrawable = ContextCompat.getDrawable(requireContext(), R.drawable.progress_bar_error)
        binding.progressBar.progressDrawable = errorDrawable
    }
    
    private fun updateOtaStatus(status: String) {
        binding.tvUpdateStatus.text = status
        
        if (status.contains("failed", ignoreCase = true) ||
            status.contains("error", ignoreCase = true)) {
            setProgressBarError()
        }
        
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
        val timestamp = SimpleDateFormat("HH:mm:ss", Locale.getDefault()).format(java.util.Date())
        val logText = "[$timestamp] $message\n"
        binding.tvLog.append(logText)
        
        binding.tvLog.post {
            val scrollView = binding.tvLog.parent as? android.widget.ScrollView
            scrollView?.let { sv ->
                val maxScrollY = sv.getChildAt(0).height - sv.height
                sv.smoothScrollTo(0, maxScrollY)
            }
        }
    }
    
    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }
}
