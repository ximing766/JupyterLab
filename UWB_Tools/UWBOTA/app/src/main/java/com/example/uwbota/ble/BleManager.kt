package com.example.uwbota.ble

import android.bluetooth.*
import android.content.Context
import android.util.Log
import kotlinx.coroutines.*
import java.nio.ByteBuffer
import java.util.*
import com.example.uwbota.utils.LogManager

/**
 * BLE Manager for handling Bluetooth Low Energy operations
 * Simplified for direct APDU frame transmission
 */
class BleManager(private val context: Context) {
    companion object {
        private const val TAG = "BleManager"
        
        // UWB OTA Service and Characteristic UUIDs (matching device-side byte order)
        private val SERVICE_UUID = UUID.fromString("D44BC439-ABFD-45A2-B575-925416129601")
        private val RX_CHARACTERISTIC_UUID = UUID.fromString("D44BC439-ABFD-45A2-B575-925416129602")
        private val TX_CHARACTERISTIC_UUID = UUID.fromString("D44BC439-ABFD-45A2-B575-925416129603")
        
        // BLE connection parameters
        private const val SCAN_TIMEOUT_MS = 10000L
        
        // BLE connection parameters
        private const val CONNECTION_TIMEOUT_MS = 10000L
        private const val OPERATION_TIMEOUT_MS = 5000L
        private const val MAX_RETRIES = 3
        private const val RETRY_DELAY_MS = 1000L
        
        // MTU configuration
        private const val DEFAULT_MTU = 23
        private const val MAX_MTU = 517
        private const val PREFERRED_MTU = 247
    }
    
    private var bluetoothAdapter: BluetoothAdapter? = null
    private var bluetoothGatt: BluetoothGatt? = null
    private var targetCharacteristic: BluetoothGattCharacteristic? = null
    
    private var currentMtu = DEFAULT_MTU
    private var isConnected = false
    private var isConnecting = false
    private var connectedDeviceAddress: String? = null
    private var descriptorWriteJob: Job? = null
    
    // Connection callbacks
    var onConnectionStateChanged: ((connected: Boolean, error: String?) -> Unit)? = null
    var onDataReceived: ((data: ByteArray) -> Unit)? = null
    var onMtuChanged: ((mtu: Int) -> Unit)? = null
    // Note: UI log messages now handled by LogManager
    
    // Scanning variables
    private var isScanning = false
    private var scanCallback: BluetoothAdapter.LeScanCallback? = null
    
    // Coroutine scope for async operations
    private val scope = CoroutineScope(Dispatchers.IO + SupervisorJob())
    
    init {
        initializeBluetooth()
    }
    
    /**
     * Initialize Bluetooth adapter
     */
    private fun initializeBluetooth() {
        val bluetoothManager = context.getSystemService(Context.BLUETOOTH_SERVICE) as BluetoothManager
        bluetoothAdapter = bluetoothManager.adapter
        
        if (bluetoothAdapter == null) {
            Log.e(TAG, "Bluetooth not supported on this device")
        } else if (!bluetoothAdapter!!.isEnabled) {
            Log.w(TAG, "Bluetooth is not enabled")
        }
    }
    
    /**
     * Connect to BLE device
     * @param deviceAddress MAC address of the target device
     */
    fun connectToDevice(deviceAddress: String) {
        val deviceName = try {
            bluetoothAdapter?.getRemoteDevice(deviceAddress)?.name ?: deviceAddress
        } catch (e: SecurityException) {
            deviceAddress
        }
        LogManager.i("正在连接设备: $deviceName")
        
        if (isConnecting || isConnected) {
            Log.w(TAG, "Already connecting or connected")
            return
        }
        
        val bluetoothAdapter = this.bluetoothAdapter
        if (bluetoothAdapter == null || !bluetoothAdapter.isEnabled) {
            Log.e(TAG, "Bluetooth not available or not enabled")
            LogManager.e("蓝牙未启用")
            onConnectionStateChanged?.invoke(false, "Bluetooth not available or not enabled")
            return
        }
        
        try {
            val device = bluetoothAdapter.getRemoteDevice(deviceAddress)
            if (device == null) {
                Log.e(TAG, "Invalid device address: $deviceAddress")
                LogManager.e("无效的设备地址")
                onConnectionStateChanged?.invoke(false, "Invalid device address: $deviceAddress")
                return
            }
            
            Log.i(TAG, "Starting connection to device: $deviceAddress")
            isConnecting = true
            connectedDeviceAddress = deviceAddress
            
            // Connect to GATT server with TRANSPORT_LE
            bluetoothGatt = device.connectGatt(context, false, gattCallback, BluetoothDevice.TRANSPORT_LE)
            
            // Set connection timeout
            scope.launch {
                delay(CONNECTION_TIMEOUT_MS)
                if (isConnecting && !isConnected) {
                    Log.w(TAG, "Connection timeout after ${CONNECTION_TIMEOUT_MS}ms")
                    LogManager.e("连接超时")
                    disconnect()
                    onConnectionStateChanged?.invoke(false, "Connection timeout")
                }
            }
            
        } catch (e: Exception) {
            Log.e(TAG, "Failed to connect to device: ${e.message}", e)
            LogManager.e("连接失败: ${e.message}")
            isConnecting = false
            onConnectionStateChanged?.invoke(false, "Connection failed: ${e.message}")
        }
    }
    
    /**
     * Disconnect from BLE device
     */
    fun disconnect() {
        LogManager.i("断开连接")
        
        isConnecting = false
        isConnected = false
        
        // Cancel any pending descriptor write timeout
        descriptorWriteJob?.cancel()
        descriptorWriteJob = null
        
        bluetoothGatt?.let { gatt ->
            Log.i(TAG, "Disconnecting from device: ${connectedDeviceAddress}")
            gatt.disconnect()
            gatt.close()
        }
        bluetoothGatt = null
        targetCharacteristic = null
        currentMtu = DEFAULT_MTU
        connectedDeviceAddress = null
        
        // Notify UI about disconnection
        onConnectionStateChanged?.invoke(false, null)
        Log.i(TAG, "Device disconnected successfully")
    }
    
    /**
     * Send APDU frame data via BLE
     * @param data APDU frame data to send
     * @return true if data was sent successfully
     */
    suspend fun sendApduFrame(data: ByteArray): Boolean {
        if (!isConnected || targetCharacteristic == null) {
            Log.e(TAG, "Not connected to device or characteristic not available")
            return false
        }
        
        return withContext(Dispatchers.IO) {
            try {
                Log.d(TAG, "Sending APDU frame: ${data.size} bytes")
                
                // Send APDU frame data directly
                val success = writeCharacteristic(data)
                
                if (success) {
                    Log.d(TAG, "APDU frame sent successfully")
                } else {
                    Log.e(TAG, "Failed to send APDU frame")
                }
                
                success
                
            } catch (e: Exception) {
                Log.e(TAG, "Error sending APDU frame: ${e.message}", e)
                false
            }
        }
    }
    
    /**
     * Write data to characteristic
     * @param data Data to write
     * @return true if write was successful
     */
    private suspend fun writeCharacteristic(data: ByteArray): Boolean {
        val characteristic = targetCharacteristic ?: return false
        val gatt = bluetoothGatt ?: return false
        
        return withContext(Dispatchers.IO) {
            try {
                @Suppress("DEPRECATION")
                characteristic.value = data
                @Suppress("DEPRECATION")
                val result = gatt.writeCharacteristic(characteristic)
                
                // #XXX OTA速率
                if (result) {
                    delay(7)
                }
                
                result
            } catch (e: Exception) {
                Log.e(TAG, "Failed to write characteristic: ${e.message}", e)
                false
            }
        }
    }
    
    /**
     * Request MTU change
     * @param mtu Desired MTU size
     */
    fun requestMtu(mtu: Int) {
        val gatt = bluetoothGatt
        if (gatt == null || !isConnected) {
            Log.w(TAG, "Cannot request MTU: not connected")
            return
        }
        
        val requestedMtu = mtu.coerceIn(DEFAULT_MTU, MAX_MTU)
        Log.i(TAG, "Requesting MTU: $requestedMtu")
        
        val result = gatt.requestMtu(requestedMtu)
        if (!result) {
            Log.e(TAG, "Failed to request MTU")
        }
    }
    
    /**
     * Get current MTU size
     */
    fun getCurrentMtu(): Int = currentMtu
    
    /**
     * Get effective data size (MTU - ATT header)
     */
    fun getEffectiveDataSize(): Int {
        // ATT header is 3 bytes (1 byte opcode + 2 bytes handle)
        return (currentMtu - 3).coerceAtLeast(20)
    }
    
    /**
     * Get connected device name
     * @return device name or address if name is not available
     */
    fun getConnectedDeviceName(): String? {
        return connectedDeviceAddress?.let { address ->
            try {
                bluetoothAdapter?.getRemoteDevice(address)?.name ?: address
            } catch (e: SecurityException) {
                address
            }
        }
    }
    
    /**
     * Check if connected to device
     */
    fun isConnected(): Boolean = isConnected
    
    /**
     * Check if connection is in progress
     */
    fun isConnecting(): Boolean = isConnecting
    
    /**
     * Start scanning for BLE devices
     */
    fun startScanning(onDeviceFound: (BluetoothDevice, Int) -> Unit) {
        val bluetoothAdapter = this.bluetoothAdapter
        if (bluetoothAdapter == null || !bluetoothAdapter.isEnabled) {
            Log.e(TAG, "Bluetooth not available or not enabled")
            LogManager.e("蓝牙未启用，无法扫描")
            return
        }
        
        if (isScanning) {
            Log.w(TAG, "Already scanning")
            return
        }
        
        LogManager.i("开始扫描蓝牙设备...")
        
        scanCallback = BluetoothAdapter.LeScanCallback { device, rssi, scanRecord ->
            // Filter out devices without names or with "Unknown" names
            val deviceName = device.name
            if (!deviceName.isNullOrBlank() && deviceName != "Unknown") {
                Log.d(TAG, "Found BLE device: ${device.address} ($deviceName) RSSI: $rssi")
                onDeviceFound(device, rssi)
            } else {
                Log.v(TAG, "Filtered out unnamed device: ${device.address} RSSI: $rssi")
            }
        }
        
        isScanning = true
        Log.i(TAG, "Starting BLE scan for all devices")
        
        @Suppress("DEPRECATION")
        bluetoothAdapter.startLeScan(scanCallback)
        
        // Stop scanning after timeout
        scope.launch {
            delay(SCAN_TIMEOUT_MS)
            stopScanning()
        }
    }
    
    /**
     * Parse service UUIDs from scan record
     */
    private fun parseServiceUuids(scanRecord: ByteArray): List<UUID> {
        val serviceUuids = mutableListOf<UUID>()
        var index = 0
        
        try {
            while (index < scanRecord.size) {
                val length = scanRecord[index].toInt() and 0xFF
                if (length == 0) break
                
                val type = scanRecord[index + 1].toInt() and 0xFF
                
                // Check for 128-bit service UUIDs (complete or incomplete)
                if ((type == 0x06 || type == 0x07) && length >= 17) {
                    val uuidBytes = ByteArray(16)
                    System.arraycopy(scanRecord, index + 2, uuidBytes, 0, 16)
                    
                    // Convert to UUID (reverse byte order for little-endian)
                    val uuid = bytesToUuid(uuidBytes)
                    serviceUuids.add(uuid)
                }
                
                index += length + 1
            }
        } catch (e: Exception) {
            Log.w(TAG, "Error parsing scan record: ${e.message}")
        }
        
        return serviceUuids
    }
    
    /**
     * Convert byte array to UUID
     */
    private fun bytesToUuid(bytes: ByteArray): UUID {
        val bb = ByteBuffer.wrap(bytes)
        val mostSigBits = bb.long
        val leastSigBits = bb.long
        return UUID(mostSigBits, leastSigBits)
    }
    
    /**
     * Stop scanning for BLE devices
     */
    fun stopScanning() {
        val bluetoothAdapter = this.bluetoothAdapter
        if (bluetoothAdapter == null || !isScanning) {
            return
        }
        
        Log.i(TAG, "Stopping BLE scan")
        isScanning = false
        
        @Suppress("DEPRECATION")
        bluetoothAdapter.stopLeScan(scanCallback)
        scanCallback = null
    }
    
    /**
     * Clean up resources
     */
    fun cleanup() {
        stopScanning()
        disconnect()
        scope.cancel()
    }
    
    /**
     * GATT callback for handling BLE events
     */
    private val gattCallback = object : BluetoothGattCallback() {

        override fun onConnectionStateChange(gatt: BluetoothGatt, status: Int, newState: Int) {
            when (newState) {
                BluetoothProfile.STATE_CONNECTED -> {
                    Log.i(TAG, "Connected to GATT server")
                    LogManager.i("设备已连接，正在发现服务...")
                    isConnecting = false
                    
                    // Discover services
                    gatt.discoverServices()
                }
                
                BluetoothProfile.STATE_DISCONNECTED -> {
                    Log.i(TAG, "Disconnected from GATT server")
                    LogManager.i("设备已断开连接")
                    isConnecting = false
                    isConnected = false
                    targetCharacteristic = null
                    currentMtu = DEFAULT_MTU
                    
                    onConnectionStateChanged?.invoke(false, null)
                }
            }
        }
        
        override fun onServicesDiscovered(gatt: BluetoothGatt, status: Int) {
            if (status == BluetoothGatt.GATT_SUCCESS) {
                Log.i(TAG, "Services discovered")
                
                // Find target service and characteristic
                val service = gatt.getService(SERVICE_UUID)
                if (service != null) {
                    targetCharacteristic = service.getCharacteristic(RX_CHARACTERISTIC_UUID)
                    
                    if (targetCharacteristic != null) {
                        Log.i(TAG, "Target characteristic found")
                        LogManager.i("OTA服务已发现")
                        
                        // Enable notifications on TX characteristic to receive data from device
                        val txCharacteristic = service.getCharacteristic(TX_CHARACTERISTIC_UUID)
                        if (txCharacteristic != null) {
                            val success = gatt.setCharacteristicNotification(txCharacteristic, true)
                            if (success) {
                                // Add small delay for some devices that need time between operations
                                scope.launch {
                                    delay(100) // 100ms delay for compatibility
                                    
                                    // Write to CCCD to enable notifications
                                     val descriptor = txCharacteristic.getDescriptor(UUID.fromString("00002902-0000-1000-8000-00805f9b34fb"))
                                     if (descriptor != null) {
                                         descriptor.value = BluetoothGattDescriptor.ENABLE_NOTIFICATION_VALUE
                                         val writeResult = gatt.writeDescriptor(descriptor)
                                         if (writeResult) {
                                             Log.i(TAG, "CCCD write initiated")
                                             
                                             // Start timeout for descriptor write
                                             descriptorWriteJob = scope.launch {
                                                 delay(5000) // 5 second timeout
                                                 Log.w(TAG, "Descriptor write timeout - assuming success for compatibility")
                                                 LogManager.i("蓝牙连接成功，已发现所需服务")
                                                 onConnectionStateChanged?.invoke(true, null)
                                             }
                                             
                                             // Connection success will be reported in onDescriptorWrite callback or timeout
                                         } else {
                                             Log.e(TAG, "Failed to initiate CCCD write")
                                             LogManager.e("通知启用失败")
                                             disconnect()
                                             onConnectionStateChanged?.invoke(false, "Failed to enable notifications")
                                         }
                                     } else {
                                         Log.w(TAG, "CCCD descriptor not found")
                                         LogManager.e("通知启用失败：描述符未找到")
                                         disconnect()
                                         onConnectionStateChanged?.invoke(false, "CCCD descriptor not found")
                                     }
                                }
                            } else {
                                Log.w(TAG, "Failed to enable notifications")
                                LogManager.e("通知启用失败")
                                disconnect()
                                onConnectionStateChanged?.invoke(false, "Failed to enable notifications")
                                return
                            }
                        } else {
                            Log.w(TAG, "TX characteristic not found")
                            LogManager.e("连接失败：TX特征未找到")
                            disconnect()
                            onConnectionStateChanged?.invoke(false, "TX characteristic not found")
                            return
                        }
                        
                        isConnected = true
                        
                        // Request preferred MTU
                        requestMtu(PREFERRED_MTU)
                        
                        // Request high connection priority for shorter connection interval (30ms)
                        val priorityResult = gatt.requestConnectionPriority(BluetoothGatt.CONNECTION_PRIORITY_HIGH)
                        if (priorityResult == true) {
                            Log.i(TAG, "Requested high connection priority for 30ms interval")
                            // onUiLog?.invoke("已请求高优先级连接（30ms间隔）")
                        } else {
                            Log.w(TAG, "Failed to request high connection priority")
                        }
                        
                        // Set preferred PHY to 2M for better performance
                        if (android.os.Build.VERSION.SDK_INT >= android.os.Build.VERSION_CODES.O) {
                            gatt.setPreferredPhy(
                                2, // PHY_LE_2M_MASK
                                2, // PHY_LE_2M_MASK
                                0  // PHY_OPTION_NO_PREFERRED
                            )
                            Log.i(TAG, "Requested 2M PHY")
                        }
                        
                        // Connection success will be reported in onDescriptorWrite callback
                        // onConnectionStateChanged?.invoke(true, null)
                    } else {
                        Log.e(TAG, "Target characteristic not found")
                        LogManager.e("连接失败：目标特征未找到")
                        disconnect()
                        onConnectionStateChanged?.invoke(false, "Target characteristic not found")
                    }
                } else {
                    Log.e(TAG, "Target service not found")
                    LogManager.e("连接失败：目标服务未找到")
                    disconnect()
                    onConnectionStateChanged?.invoke(false, "Target service not found")
                }
            } else {
                Log.e(TAG, "Service discovery failed with status: $status")
                LogManager.e("连接失败：服务发现失败")
                disconnect()
                onConnectionStateChanged?.invoke(false, "Service discovery failed")
            }
        }
        
        @Suppress("DEPRECATION")
        override fun onCharacteristicRead(gatt: BluetoothGatt, characteristic: BluetoothGattCharacteristic, status: Int) {
            if (status == BluetoothGatt.GATT_SUCCESS) {
                val data = characteristic.value
                if (data != null) {
                    Log.d(TAG, "Characteristic read: ${data.size} bytes")
                    onDataReceived?.invoke(data)
                }
            }
        }
        
        override fun onCharacteristicWrite(gatt: BluetoothGatt, characteristic: BluetoothGattCharacteristic, status: Int) {
            if (status == BluetoothGatt.GATT_SUCCESS) {
                Log.d(TAG, "Characteristic write successful")
            } else {
                Log.e(TAG, "Characteristic write failed with status: $status")
            }
        }
        
        @Suppress("DEPRECATION")
        override fun onCharacteristicChanged(gatt: BluetoothGatt, characteristic: BluetoothGattCharacteristic) {
            val data = characteristic.value
            if (data != null) {
                Log.d(TAG, "Characteristic changed: ${data.size} bytes")
                onDataReceived?.invoke(data)
            }
        }
        
        override fun onMtuChanged(gatt: BluetoothGatt, mtu: Int, status: Int) {
            if (status == BluetoothGatt.GATT_SUCCESS) {
                Log.i(TAG, "MTU changed to: $mtu")
                currentMtu = mtu
                onMtuChanged?.invoke(mtu)
            } else {
                Log.e(TAG, "MTU change failed with status: $status")
            }
        }
        
        override fun onDescriptorWrite(gatt: BluetoothGatt, descriptor: BluetoothGattDescriptor, status: Int) {
            // Cancel the timeout job since we got the callback
            descriptorWriteJob?.cancel()
            descriptorWriteJob = null
            
            if (status == BluetoothGatt.GATT_SUCCESS) {
                Log.i(TAG, "Descriptor write successful - CCCD enabled")
                LogManager.i("蓝牙连接成功，已发现所需服务")
                onConnectionStateChanged?.invoke(true, null)
            } else {
                Log.e(TAG, "Descriptor write failed with status: $status")
                LogManager.e("通知启用失败，状态码: $status")
                // Try to reconnect or handle the error
                disconnect()
                onConnectionStateChanged?.invoke(false, "Failed to enable notifications")
            }
        }
        
        override fun onPhyUpdate(gatt: BluetoothGatt, txPhy: Int, rxPhy: Int, status: Int) {
            if (status == BluetoothGatt.GATT_SUCCESS) {
                val txPhyStr = when (txPhy) {
                    1 -> "1M"    // PHY_LE_1M
                    2 -> "2M"    // PHY_LE_2M
                    3 -> "Coded" // PHY_LE_CODED
                    else -> "Unknown($txPhy)"
                }
                val rxPhyStr = when (rxPhy) {
                    1 -> "1M"    // PHY_LE_1M
                    2 -> "2M"    // PHY_LE_2M
                    3 -> "Coded" // PHY_LE_CODED
                    else -> "Unknown($rxPhy)"
                }
                Log.i(TAG, "PHY updated - TX: $txPhyStr, RX: $rxPhyStr")
                LogManager.i("PHY已更新 - TX: $txPhyStr, RX: $rxPhyStr")
            } else {
                Log.e(TAG, "PHY update failed with status: $status")
                LogManager.e("PHY更新失败")
            }
        }
    }
}