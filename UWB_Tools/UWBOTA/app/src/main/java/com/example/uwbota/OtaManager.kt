package com.example.uwbota

import android.content.Context
import android.net.Uri
import android.util.Log
import kotlinx.coroutines.*
import java.io.InputStream
import kotlin.math.min
import com.example.uwbota.ble.BleManager
import com.example.uwbota.ApduProtocol
import com.example.uwbota.FirmwareHeader
import com.example.uwbota.utils.LogManager

/**
 * OTA Manager for handling firmware upgrade process
 * Integrates firmware processing, APDU protocol, and BLE transmission
 */
class OtaManager(
    private val context: Context,
    private val bleManager: BleManager
) {
    
    private val apduProtocol = ApduProtocol()
    private var otaJob: Job? = null
    
    // OTA configuration - Based on UWB_OTA_PLAN_INTRO.md
    private val appFirmwareStartAddress = 0x280000  // External Flash App firmware storage area
    private val sr150FirmwareStartAddress = 0x300000  // External Flash SR150 firmware storage area
    private val maxRetries = 3
    private val transmissionDelay = 100L // ms between transmissions
    
    // OTA state variables
    private var isOtaInProgress = false
    private var currentProgress = 0
    private var otaStartTime = 0L  // Record OTA start time
    
    // OTA confirmation waiting flags
    private var isWaitingForEraseConfirmation = false  // Flag to track erase confirmation waiting
    private var isWaitingForProgramConfirmation = false  // Flag to track program confirmation waiting
    private var isWaitingForVerifyConfirmation = false
    private var verificationResult = false // Track verification result  // Flag to track verify confirmation waiting
    
    // Packet loss detection and retransmission
    private var isPacketLossDetected = false
    private var expectedPageNumber = 0
    private var retransmissionStartIndex = 0
    
    // Duplicate response prevention
    private var lastProcessedPageNumber = -1
    private var lastProcessedTime = 0L
    private val duplicatePreventionTimeoutMs = 1000L // 1 second
    
    // Transfer speed calculation variables
    private var totalBytesToTransfer = 0
    private var bytesTransferred = 0
    private var lastSpeedUpdateTime = 0L
    private var lastBytesTransferred = 0
    private var currentTransferSpeed = 0.0 // KB/s
    private var retryCount = 0 // Track retry count for statistics
    
    var onProgressUpdate: ((progress: Int, total: Int, message: String?, speed: String?, transferred: Long, totalBytes: Long) -> Unit)? = null
    var onStatusUpdate: ((status: String?) -> Unit)? = null
    var onOtaComplete: ((success: Boolean, message: String) -> Unit)? = null
    
    /**
     * Start OTA firmware upgrade process
     * @param firmwareUri URI of the firmware file
     * @param firmwareType Type of firmware (APP or SR150)
     */
    fun startOtaUpgrade(firmwareUri: Uri, firmwareType: FirmwareType = FirmwareType.APP_FIRMWARE) {
        // Cancel any existing OTA operation
        cancelOtaUpgrade()
        
        otaJob = CoroutineScope(Dispatchers.IO).launch {
            try {
                performOtaUpgrade(firmwareUri, firmwareType)
            } catch (e: Exception) {
                isOtaInProgress = false
                val otaEndTime = System.currentTimeMillis()
                val otaDuration = otaEndTime - otaStartTime
                val durationSeconds = otaDuration / 1000.0
                
                withContext(Dispatchers.Main) {
                    LogManager.e("OTA升级失败: ${e.message}")
                    // LogManager.i("OTA耗时: ${String.format("%.2f", durationSeconds)}秒")
                    onOtaComplete?.invoke(false, "OTA升级失败: ${e.message}")
                }
                otaStartTime = 0L
            }
        }
    }
    

    fun cancelOtaUpgrade() {
        if (isOtaInProgress && otaStartTime > 0) {
            val otaEndTime = System.currentTimeMillis()
            val otaDuration = otaEndTime - otaStartTime
            val durationSeconds = otaDuration / 1000.0
            LogManager.i("OTA升级已取消")
            // LogManager.i("OTA耗时: ${String.format("%.2f", durationSeconds)}秒")
        }
        
        otaJob?.cancel()
        otaJob = null
        isOtaInProgress = false
        otaStartTime = 0L
    }
    
    fun isOtaInProgress(): Boolean {
        return otaJob?.isActive == true
    }
    
    /**
     * Perform the actual OTA upgrade process
     * @param firmwareUri URI of the firmware file
     * @param firmwareType Type of firmware (APP or SR150)
     */
    private suspend fun performOtaUpgrade(firmwareUri: Uri, firmwareType: FirmwareType) {
        isOtaInProgress = true
        currentProgress = 0
        otaStartTime = System.currentTimeMillis()  // Record start time
        
        // Initialize transfer speed variables
        totalBytesToTransfer = 0
        bytesTransferred = 0
        lastSpeedUpdateTime = otaStartTime
        lastBytesTransferred = 0
        currentTransferSpeed = 0.0
        
        withContext(Dispatchers.Main) {
            onStatusUpdate?.invoke("正在读取${firmwareType.displayName}文件...")
            LogManager.i("=== 开始${firmwareType.displayName}升级 ===")
        }
        
        // Handle different firmware types
        if (firmwareType == FirmwareType.SR150_FIRMWARE) {
            // SR150 firmware uses different processing logic
            performSR150OtaUpgrade(firmwareUri)
            return
        }
        
        // Step 1: Read firmware file
        val firmwareData = readFirmwareFile(firmwareUri)
        
        withContext(Dispatchers.Main) {
            LogManager.i("固件文件大小: ${firmwareData.size} 字节")
        }
        
        // Step 2: Create firmware header
        val firmwareHeader = FirmwareHeader.createFromFirmware(firmwareData, version = 0x0001)
        val headerData = firmwareHeader.toByteArray()
        
        withContext(Dispatchers.Main) {
            LogManager.i("固件头部: 版本=${firmwareHeader.getVersionString()}, CRC32=0x${firmwareHeader.crc32.toString(16).uppercase()}")
        }
        
        // Step 3: Combine header and firmware data
        val completeData = headerData + firmwareData
        val firmwareSize = completeData.size
        totalBytesToTransfer = firmwareSize  // Set total bytes for speed calculation
        
        withContext(Dispatchers.Main) {
            LogManager.i("完整固件大小: $firmwareSize 字节 (含头部)")
        }
        
        // Step 2: Calculate erase parameters
        val sectorsNeeded = apduProtocol.calculateSectorsNeeded(firmwareSize)
        
        // Step 4: Split firmware into 128-byte chunks
        val firmwareChunks = apduProtocol.splitFirmwareData(completeData)
        
        withContext(Dispatchers.Main) {
            LogManager.i("固件分块: ${firmwareChunks.size}个128字节块")
            // onStatusUpdate?.invoke("开始擦除Flash...")
        }
        
        // Step 5: Erase flash sectors
        executeErasePhase(sectorsNeeded, firmwareType)
        
        // Step 6: Program firmware data
        withContext(Dispatchers.Main) {
            onStatusUpdate?.invoke("开始写入固件...")
        }
        
        executeProgramPhase(firmwareChunks, firmwareType)
        
        // Step 7: Verify firmware (read header)
        withContext(Dispatchers.Main) {
            onStatusUpdate?.invoke("正在验证固件...")
        }
        
        executeVerifyPhase(firmwareType)
        
        // Step 8: Complete
        val otaEndTime = System.currentTimeMillis()
        val otaDuration = otaEndTime - otaStartTime
        val durationSeconds = otaDuration / 1000.0
        
        // Check verification result before proceeding
        if (!verificationResult) {
            withContext(Dispatchers.Main) {
                onStatusUpdate?.invoke("OTA升级失败")
                LogManager.e("固件验证失败，停止升级流程")
                onOtaComplete?.invoke(false, "固件验证失败，升级终止")
            }
            isOtaInProgress = false
            otaStartTime = 0L
            return
        }

        withContext(Dispatchers.Main) {
            onStatusUpdate?.invoke("OTA升级完成")
            LogManager.i("固件升级成功,重启设备...")
            onOtaComplete?.invoke(true, "固件升级成功")
        }

        // Step 9: Reset MCU
        withContext(Dispatchers.Main) {
            onStatusUpdate?.invoke("重置MCU...")
        }
        resetDevice()
        
        isOtaInProgress = false
        otaStartTime = 0L
    }
    
    private suspend fun readFirmwareFile(firmwareUri: Uri): ByteArray {
        return withContext(Dispatchers.IO) {
            context.contentResolver.openInputStream(firmwareUri)?.use { inputStream ->
                inputStream.readBytes()
            } ?: throw Exception("无法读取固件文件")
        }
    }
    
    private suspend fun executeErasePhase(sectorsNeeded: Int, firmwareType: FirmwareType) {
        withContext(Dispatchers.Main) {
            LogManager.i("=== 阶段1: Flash擦除 ===")
            onProgressUpdate?.invoke(0, 100, "开始擦除Flash...", null, 0L, totalBytesToTransfer.toLong())
        }
        
        // Calculate blocks to erase (64KB blocks)
        val blocksToErase = apduProtocol.calculateBlocksNeeded(sectorsNeeded * ApduProtocol.W25Q32JV_SECTOR_SIZE)
        
        withContext(Dispatchers.Main) {
            LogManager.i("擦除Flash块: 起始地址=0x${firmwareType.startAddress.toString(16).uppercase()}, 块数=$blocksToErase")
        }
        
        // Build erase command packet - send start address and block count in one command
        val erasePacket = apduProtocol.buildProtocolPacket(
            command = ApduProtocol.FIRMWARE_ERASE,
            address = firmwareType.startAddress,
            blockCount = blocksToErase
        )
        
        // Send erase command with retry mechanism
        for (retry in 0 until maxRetries) {
            try {
                bleManager.sendApduFrame(erasePacket)
                break
            } catch (e: Exception) {
                if (retry == maxRetries - 1) {
                    throw Exception("擦除Flash块失败 (地址: 0x${firmwareType.startAddress.toString(16)}, 块数: $blocksToErase): ${e.message}")
                }
                withContext(Dispatchers.Main) {
                        LogManager.w("擦除重试 ${retry + 1}/$maxRetries")
                    }
                delay(500) // Wait before retry
            }
        }

        withContext(Dispatchers.Main) {
            onProgressUpdate?.invoke(10, 100, "等待擦除确认...", null, 0L, totalBytesToTransfer.toLong())
        }
        
        // Set flag to wait for erase confirmation
        isWaitingForEraseConfirmation = true
        
        // Wait for erase confirmation with timeout
        val startTime = System.currentTimeMillis()
        val timeoutMs = 15000L // 15 seconds timeout
        
        while (isWaitingForEraseConfirmation && (System.currentTimeMillis() - startTime) < timeoutMs) {
            delay(100) // Check every 100ms
        }
        
        if (isWaitingForEraseConfirmation) {
            // Timeout occurred
            isWaitingForEraseConfirmation = false
            withContext(Dispatchers.Main) {
                LogManager.w("警告：未收到擦除确认包，继续执行写入操作")
            }
        }
    }
    
    private suspend fun executeProgramPhase(firmwareChunks: List<ByteArray>, firmwareType: FirmwareType) {
        withContext(Dispatchers.Main) {
            LogManager.i("=== 阶段2: 固件写入 ===")
            LogManager.i("固件块总数: ${firmwareChunks.size}")
        }
        
        var currentAddress = firmwareType.startAddress
        val totalChunks = firmwareChunks.size
        
        // Sending statistics for monitoring
        var packetCount = 0 // Counter for sent packets
        var totalSentBytes = 0
        val sendStartTime = System.currentTimeMillis()
        
        // Reset packet loss detection variables at start of program phase
        isPacketLossDetected = false
        expectedPageNumber = 0
        retransmissionStartIndex = 0
        
        // Reset duplicate prevention variables
        lastProcessedPageNumber = -1
        lastProcessedTime = 0L
        
        var chunkIndex = 0
        var allPacketsSent = false
        
        while (!allPacketsSent) {
            // Send packets from current chunkIndex to end
            while (chunkIndex < firmwareChunks.size) {
                // Check for packet loss and handle retransmission
                if (isPacketLossDetected) {
                    withContext(Dispatchers.Main) {
                    LogManager.w("开始从页号 $retransmissionStartIndex 重发数据")
                }
                    chunkIndex = retransmissionStartIndex
                    // Recalculate current address for retransmission
                    currentAddress = firmwareType.startAddress + (chunkIndex * ApduProtocol.FLASH_ALIGNED_CHUNK_SIZE)
                    isPacketLossDetected = false
                }
                
                val chunk = firmwareChunks[chunkIndex]
                
                // Calculate progress: 10% (erase) + 80% (program) + 10% (verify)
                // Program phase progress: 10% to 90%
                val programProgress = 10 + ((chunkIndex + 1) * 80 / totalChunks)
                
                // Update bytes transferred and calculate speed
                bytesTransferred += chunk.size
                val currentTime = System.currentTimeMillis()
                var speedText: String? = null
                
                // Calculate speed every 1 second or every 10 chunks
                if (currentTime - lastSpeedUpdateTime >= 1000 || chunkIndex % 10 == 0) {
                    val timeDiff = (currentTime - lastSpeedUpdateTime) / 1000.0
                    val bytesDiff = bytesTransferred - lastBytesTransferred
                    
                    if (timeDiff > 0) {
                        currentTransferSpeed = (bytesDiff / 1024.0) / timeDiff // KB/s
                        speedText = String.format("%.1f KB/s", currentTransferSpeed)
                        
                        lastSpeedUpdateTime = currentTime
                        lastBytesTransferred = bytesTransferred
                    }
                } else if (currentTransferSpeed > 0) {
                    speedText = String.format("%.1f KB/s", currentTransferSpeed)
                }
                
                withContext(Dispatchers.Main) {
                    // Log only on first send and every 8th send (1K data)
                    if (chunkIndex == 0 || chunkIndex % 16 == 0) {
                        LogManager.d(
                            "${chunkIndex + 1}/$totalChunks: 0x${currentAddress.toString(16).uppercase()} " +
                            "(${chunk.size}B)"
                        )
                    }
                    onProgressUpdate?.invoke(
                        programProgress, 
                        100, 
                        null,
                        speedText,
                        bytesTransferred.toLong(),
                        totalBytesToTransfer.toLong()
                    )
                }
                
                // Build 128-byte firmware program packet
                // Calculate pages: 128 bytes = 1 page (128 bytes per page)
                val pages = (chunk.size + ApduProtocol.FLASH_ALIGNED_CHUNK_SIZE - 1) / ApduProtocol.FLASH_ALIGNED_CHUNK_SIZE
                val programPacket = apduProtocol.buildProtocolPacket(
                    command = ApduProtocol.FIRMWARE_PROGRAM,
                    address = currentAddress,
                    data = chunk,
                    pages = pages,
                    pageNumber = chunkIndex
                )
                
                // Send program command with retry mechanism
                for (retry in 0 until maxRetries) {
                    try {
                        bleManager.sendApduFrame(programPacket)
                        totalSentBytes += chunk.size // Update sent bytes statistics
                        break
                    } catch (e: Exception) {
                        retryCount++ // Update retry statistics
                        if (retry == maxRetries - 1) {
                            throw Exception("写入固件失败 (地址: 0x${currentAddress.toString(16)}): ${e.message}")
                        }
                        withContext(Dispatchers.Main) {
                            LogManager.w("写入重试 ${retry + 1}/$maxRetries")
                        }
                        delay(500) // Wait before retry
                    }
                }
                
                packetCount++
                currentAddress += ApduProtocol.FLASH_ALIGNED_CHUNK_SIZE
                
                // If packet loss detected, don't increment chunkIndex to retry from expected page
                if (!isPacketLossDetected) {
                    chunkIndex++
                }
            }
            
            // All packets sent, now wait and check for packet loss
            withContext(Dispatchers.Main) {
                LogManager.i("所有包已发送，等待1秒检查丢包...")
            }
            
            delay(1000) // Wait 1 second for potential packet loss notifications
            
            if (isPacketLossDetected) {
                withContext(Dispatchers.Main) {
                    LogManager.w("检测到丢包，准备重发从页号 $retransmissionStartIndex 开始的数据")
                }
                // Reset for retransmission
                chunkIndex = retransmissionStartIndex
                currentAddress = firmwareType.startAddress + (chunkIndex * ApduProtocol.FLASH_ALIGNED_CHUNK_SIZE)
                isPacketLossDetected = false
            } else {
                // all packets successfully sent
                allPacketsSent = true
            }
        }
        
        // Calculate and display sending statistics
        val sendEndTime = System.currentTimeMillis()
        val totalSendTime = (sendEndTime - sendStartTime) / 1000.0 // seconds
        val averageSpeed = if (totalSendTime > 0) (totalSentBytes / 1024.0) / totalSendTime else 0.0 // KB/s
        
        withContext(Dispatchers.Main) {
            LogManager.i("固件写入完成")
            LogManager.i("=== 统计信息 ===")
            LogManager.i("总包数: $packetCount")
            LogManager.i("总字节数: ${totalSentBytes}B (${String.format("%.1f", totalSentBytes / 1024.0)}KB)")
            LogManager.i("重试次数: $retryCount")
            LogManager.i("总耗时: ${String.format("%.1f", totalSendTime)}秒")
            LogManager.i("平均速度: ${String.format("%.1f", averageSpeed)}KB/s")
            if (retryCount > 0) {
                val retryRate = (retryCount.toDouble() / packetCount) * 100
                LogManager.i("重试率: ${String.format("%.1f", retryRate)}%")
                retryCount = 0
            }
        }
       
    }
    
    private suspend fun executeVerifyPhase(firmwareType: FirmwareType) {
        // Reset verification result at the start of verification phase
        verificationResult = false
        
        withContext(Dispatchers.Main) {
            LogManager.i("=== 阶段3: 固件验证 ===")
            onProgressUpdate?.invoke(90, 100, "开始验证固件...", null, totalBytesToTransfer.toLong(), totalBytesToTransfer.toLong())
        }
        
        // Build read header command packet
        val readHeaderPacket = apduProtocol.buildProtocolPacket(
            command = ApduProtocol.FIRMWARE_READ_HEADER,
            address = firmwareType.startAddress
        )
        
        // Send read header command
        try {
            bleManager.sendApduFrame(readHeaderPacket)
            
            withContext(Dispatchers.Main) {
            onProgressUpdate?.invoke(95, 100, "等待验证确认...", null, totalBytesToTransfer.toLong(), totalBytesToTransfer.toLong())
        }
            
            // Set flag to wait for verify confirmation
            isWaitingForVerifyConfirmation = true
            
            // Wait for verify confirmation with timeout
            val startTime = System.currentTimeMillis()
            val timeoutMs = 5000L // 5 seconds timeout
            
            while (isWaitingForVerifyConfirmation && (System.currentTimeMillis() - startTime) < timeoutMs) {
                delay(100) // Check every 100ms
            }
            
            if (isWaitingForVerifyConfirmation) {
                // Timeout occurred
                isWaitingForVerifyConfirmation = false
                verificationResult = false // Set verification as failed on timeout
                withContext(Dispatchers.Main) {
                    LogManager.e("验证超时：未收到验证确认包，验证失败")
                }
            }
            
            withContext(Dispatchers.Main) {
                onProgressUpdate?.invoke(100, 100, "验证完成", null, totalBytesToTransfer.toLong(), totalBytesToTransfer.toLong())
            }
            
        } catch (e: Exception) {
            verificationResult = false // Set verification as failed on exception
            withContext(Dispatchers.Main) {
                LogManager.e("固件头验证命令发送失败: ${e.message}")
                onProgressUpdate?.invoke(100, 100, "验证失败", null, totalBytesToTransfer.toLong(), totalBytesToTransfer.toLong())
            }
        }
    }

    suspend fun resetDevice() {
        val resetPacket = apduProtocol.buildProtocolPacket(
            command = ApduProtocol.RESET_MCU
        )
        
        try {
            bleManager.sendApduFrame(resetPacket)
        } catch (e: Exception) {
            withContext(Dispatchers.Main) {
                LogManager.e("复位命令发送失败: ${e.message}")
            }
        }
    }

    /**
     * Handle received BLE data, check for OTA confirmation packets
     * Format: [phase, status/expected_page] where:
     * - phase: 0x01=erase, 0x02=program, 0x03=verify, 0x04=packet_loss_error
     * - status: 0x00=success, 0x01=failure (for phases 1-3)
     * - expected_page: expected page number (for phase 4)
     */
    fun handleReceivedData(data: ByteArray) {
        if (data.size >= 2) {
            val phase = data[0]
            val statusOrPage = data[1]
            
            when (phase) {
                0x01.toByte() -> { // Erase confirmation
                    if (isWaitingForEraseConfirmation) {
                        isWaitingForEraseConfirmation = false
                        val success = statusOrPage == 0x00.toByte()
                        CoroutineScope(Dispatchers.Main).launch {
                            if (success) {
                                LogManager.i("收到擦除确认包：擦除成功")
                            } else {
                                LogManager.e("收到擦除确认包：擦除失败")
                            }
                        }
                    }
                }
                0x02.toByte() -> { // Program confirmation
                    if (isWaitingForProgramConfirmation) {
                        isWaitingForProgramConfirmation = false
                        val success = statusOrPage == 0x00.toByte()
                        CoroutineScope(Dispatchers.Main).launch {
                            if (success) {
                                LogManager.i("收到写入确认包：写入成功")
                            } else {
                                LogManager.e("收到写入确认包：写入失败")
                            }
                        }
                    }
                }
                0x03.toByte() -> { // Verify confirmation
                    if (isWaitingForVerifyConfirmation) {
                        isWaitingForVerifyConfirmation = false
                        verificationResult = statusOrPage == 0x00.toByte()
                        CoroutineScope(Dispatchers.Main).launch {
                            if (verificationResult) {
                                // LogManager.i("收到验证确认包：验证成功")
                            } else {
                                LogManager.e("收到验证确认包：验证失败")
                            }
                        }
                    }
                }
                0x04.toByte() -> { // Packet loss error
                    // Read two bytes for page number: page = (data[2] << 8) | data[1]
                    if (data.size >= 3) {
                        expectedPageNumber = (data[1].toInt() and 0xFF) or ((data[2].toInt() and 0xFF) shl 8)
                    } else {
                        expectedPageNumber = statusOrPage.toInt() and 0xFF // Fallback for single byte
                    }
                    
                    // Prevent duplicate processing of the same page number within 1 second
                    val currentTime = System.currentTimeMillis()
                    if (expectedPageNumber == lastProcessedPageNumber && 
                        (currentTime - lastProcessedTime) < duplicatePreventionTimeoutMs) {
                        // Ignore duplicate response for the same page number within timeout
                        return
                    }
                    
                    // Update last processed info
                    lastProcessedPageNumber = expectedPageNumber
                    lastProcessedTime = currentTime
                    
                    isPacketLossDetected = true
                    retransmissionStartIndex = expectedPageNumber
                    
                    CoroutineScope(Dispatchers.Main).launch {
                        retryCount++ 
                        LogManager.w("检测到丢包，设备期待页号: $expectedPageNumber，准备重发")
                    }
                }
            }
        }
    }

    /**
     * Perform SR150 firmware upgrade with special handling
     * SR150 firmware uses CRC16-XMODEM and writes config to 0x00300000
     */
    private suspend fun performSR150OtaUpgrade(firmwareUri: Uri) {
        withContext(Dispatchers.Main) {
            onStatusUpdate?.invoke("正在读取SR150固件文件...")
        }
        
        // Step 1: Read firmware file
        val firmwareData = readFirmwareFile(firmwareUri)
        
        // Step 2: Create SR150 firmware header (CRC16 + size)
        val sr150Header = SR150FirmwareHeader.createFromFirmware(firmwareData)
        
        withContext(Dispatchers.Main) {
            LogManager.i("SR150固件头部: CRC16=0x${sr150Header.crc16.toString(16).uppercase().padStart(4, '0')}, 大小=${sr150Header.size}")
        }
        
        // Step 3: Create complete firmware package (header + firmware data)
        val headerData = sr150Header.getConfigData()  // 256 bytes header
        val completePackage = headerData + firmwareData  // Header at 0x300000, firmware at 0x300100
        
        // Step 4: Calculate firmware parameters
        totalBytesToTransfer = completePackage.size
        
        // Step 5: Calculate erase parameters for complete package
        val sectorsNeeded = apduProtocol.calculateSectorsNeeded(completePackage.size)
        
        // Step 6: Split complete package into 128-byte chunks
        val firmwareChunks = apduProtocol.splitFirmwareData(completePackage)
        
        withContext(Dispatchers.Main) {
            LogManager.i("SR150完整包分块: ${firmwareChunks.size}个128字节块")
        }
        
        // Step 7: Erase flash sectors for complete package
        executeSR150ErasePhase(sectorsNeeded)
        
        // Step 8: Program complete package (header + firmware)
        withContext(Dispatchers.Main) {
            onStatusUpdate?.invoke(null)
        }
        
        executeSR150ProgramPhase(firmwareChunks)
        
        // Step 9: Complete
        val otaEndTime = System.currentTimeMillis()
        val otaDuration = otaEndTime - otaStartTime
        val durationSeconds = otaDuration / 1000.0
        
        withContext(Dispatchers.Main) {
            onStatusUpdate?.invoke("SR150固件升级完成")
            LogManager.i("SR150固件升级成功，耗时: ${String.format("%.1f", durationSeconds)}秒")
            LogManager.i("固件头部地址: 0x${FirmwareType.SR150_FIRMWARE.startAddress.toString(16).uppercase()}")
            LogManager.i("固件数据地址: 0x${(FirmwareType.SR150_FIRMWARE.startAddress + SR150FirmwareHeader.CONFIG_SIZE).toString(16).uppercase()}")
            onOtaComplete?.invoke(true, "SR150固件升级成功")
        }
        
        isOtaInProgress = false
        otaStartTime = 0L
    }
    
    /**
     * Execute SR150 firmware erase phase
     */
    private suspend fun executeSR150ErasePhase(sectorsNeeded: Int) {
        withContext(Dispatchers.Main) {
            LogManager.i("=== SR150阶段1: Flash擦除 ===")
            onProgressUpdate?.invoke(0, 100, "开始擦除SR150 Flash...", null, 0L, totalBytesToTransfer.toLong())
        }
        
        // Calculate blocks to erase for SR150 firmware area
        val blocksToErase = apduProtocol.calculateBlocksNeeded(sectorsNeeded * ApduProtocol.W25Q32JV_SECTOR_SIZE)
        
        // Build erase command packet for SR150 firmware area
        val erasePacket = apduProtocol.buildProtocolPacket(
            command = ApduProtocol.FIRMWARE_ERASE,
            address = FirmwareType.SR150_FIRMWARE.startAddress,
            blockCount = blocksToErase
        )
        
        // Send erase command with retry mechanism
        for (retry in 0 until maxRetries) {
            try {
                bleManager.sendApduFrame(erasePacket)
                break
            } catch (e: Exception) {
                if (retry == maxRetries - 1) {
                    throw Exception("擦除SR150 Flash块失败 (地址: 0x${FirmwareType.SR150_FIRMWARE.startAddress.toString(16)}, 块数: $blocksToErase): ${e.message}")
                }
                withContext(Dispatchers.Main) {
                    LogManager.w("SR150擦除重试 ${retry + 1}/$maxRetries")
                }
                delay(500)
            }
        }
        
        withContext(Dispatchers.Main) {
            onProgressUpdate?.invoke(10, 100, "等待SR150擦除确认...", null, 0L, totalBytesToTransfer.toLong())
        }
        
        // Wait for erase confirmation
        isWaitingForEraseConfirmation = true
        val startTime = System.currentTimeMillis()
        val timeoutMs = 15000L
        
        while (isWaitingForEraseConfirmation && (System.currentTimeMillis() - startTime) < timeoutMs) {
            delay(100)
        }
        
        if (isWaitingForEraseConfirmation) {
            isWaitingForEraseConfirmation = false
            withContext(Dispatchers.Main) {
                LogManager.w("警告：未收到SR150擦除确认包，继续执行写入操作")
            }
        }
    }
    
    /**
     * Execute SR150 firmware program phase (complete package with header + firmware data)
     */
    private suspend fun executeSR150ProgramPhase(firmwareChunks: List<ByteArray>) {
        withContext(Dispatchers.Main) {
            LogManager.i("=== SR150阶段2: 固件头+固件数据 ===")
        }
        
        var currentAddress = FirmwareType.SR150_FIRMWARE.startAddress
        val totalChunks = firmwareChunks.size
        
        // Reset packet loss detection variables
        isPacketLossDetected = false
        expectedPageNumber = 0
        retransmissionStartIndex = 0
        lastProcessedPageNumber = -1
        lastProcessedTime = 0L
        
        var chunkIndex = 0
        var allPacketsSent = false
        
        while (!allPacketsSent) {
            // Send packets from current chunkIndex to end
            while (chunkIndex < firmwareChunks.size) {
                // Handle packet loss retransmission
                if (isPacketLossDetected) {
                    withContext(Dispatchers.Main) {
                        LogManager.w("SR150开始从页号 $retransmissionStartIndex 重发数据")
                    }
                    chunkIndex = retransmissionStartIndex
                    currentAddress = FirmwareType.SR150_FIRMWARE.startAddress + (chunkIndex * ApduProtocol.FLASH_ALIGNED_CHUNK_SIZE)
                    isPacketLossDetected = false
                }
                
                val chunk = firmwareChunks[chunkIndex]
                
                // Calculate progress: 10% (erase) + 90% (program)
                val programProgress = 10 + ((chunkIndex + 1) * 90 / totalChunks)
                
                // Update bytes transferred and calculate speed
                bytesTransferred += chunk.size
                val currentTime = System.currentTimeMillis()
                var speedText: String? = null
                
                if (currentTime - lastSpeedUpdateTime >= 1000 || chunkIndex % 10 == 0) {
                    val timeDiff = (currentTime - lastSpeedUpdateTime) / 1000.0
                    val bytesDiff = bytesTransferred - lastBytesTransferred
                    
                    if (timeDiff > 0) {
                        currentTransferSpeed = (bytesDiff / 1024.0) / timeDiff
                        speedText = String.format("%.1f KB/s", currentTransferSpeed)
                        
                        lastSpeedUpdateTime = currentTime
                        lastBytesTransferred = bytesTransferred
                    }
                } else if (currentTransferSpeed > 0) {
                    speedText = String.format("%.1f KB/s", currentTransferSpeed)
                }
                
                withContext(Dispatchers.Main) {
                    if (chunkIndex == 0 || chunkIndex % 16 == 0) {
                        LogManager.d(
                            "SR150 ${chunkIndex + 1}/$totalChunks: 0x${currentAddress.toString(16).uppercase()} " +
                            "(${chunk.size}B)"
                        )
                    }
                    onProgressUpdate?.invoke(
                        programProgress,
                        100,
                        null,
                        speedText,
                        bytesTransferred.toLong(),
                        totalBytesToTransfer.toLong()
                    )
                }
                
                // Build SR150 firmware program packet
                val pages = (chunk.size + ApduProtocol.FLASH_ALIGNED_CHUNK_SIZE - 1) / ApduProtocol.FLASH_ALIGNED_CHUNK_SIZE
                val programPacket = apduProtocol.buildProtocolPacket(
                    command = ApduProtocol.FIRMWARE_PROGRAM,
                    address = currentAddress,
                    data = chunk,
                    pages = pages,
                    pageNumber = chunkIndex
                )
                
                // Send program command with retry mechanism
                for (retry in 0 until maxRetries) {
                    try {
                        bleManager.sendApduFrame(programPacket)
                        break
                    } catch (e: Exception) {
                        if (retry == maxRetries - 1) {
                            throw Exception("写入SR150完整包失败 (地址: 0x${currentAddress.toString(16)}): ${e.message}")
                        }
                        withContext(Dispatchers.Main) {
                            LogManager.w("SR150写入重试 ${retry + 1}/$maxRetries")
                        }
                        delay(500)
                    }
                }
                
                currentAddress += ApduProtocol.FLASH_ALIGNED_CHUNK_SIZE
                
                if (!isPacketLossDetected) {
                    chunkIndex++
                }
            }
            
            // All packets sent, now wait and check for packet loss
            withContext(Dispatchers.Main) {
                LogManager.i("SR150所有包已发送，等待1秒检查丢包...")
            }
            
            delay(1000) // Wait 1 second for potential packet loss notifications
            
            if (isPacketLossDetected) {
                withContext(Dispatchers.Main) {
                    LogManager.w("SR150检测到丢包，准备重发从页号 $retransmissionStartIndex 开始的数据")
                }
                // Reset for retransmission
                chunkIndex = retransmissionStartIndex
                currentAddress = FirmwareType.SR150_FIRMWARE.startAddress + (chunkIndex * ApduProtocol.FLASH_ALIGNED_CHUNK_SIZE)
                isPacketLossDetected = false
            } else {
                // No packet loss detected, all packets successfully sent
                allPacketsSent = true
                withContext(Dispatchers.Main) {
                    LogManager.i("SR150未检测到丢包，所有数据包发送完成")
                }
            }
        }
        
        withContext(Dispatchers.Main) {
            LogManager.i("SR150完整包写入完成")
        }
    }
    


    companion object {
        private const val TAG = "OtaManager"
        
        // OTA operation timeouts
        private const val COMMAND_TIMEOUT_MS = 5000L
        private const val ERASE_TIMEOUT_MS = 30000L
        private const val PROGRAM_TIMEOUT_MS = 10000L
        
        // Retry configuration
        private const val MAX_RETRIES = 3
        private const val RETRY_DELAY_MS = 1000L
    }
}