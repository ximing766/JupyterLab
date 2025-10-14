package com.example.uwbota

import java.io.ByteArrayOutputStream
import java.nio.ByteBuffer
import java.nio.ByteOrder
import com.example.uwbota.utils.LogManager

/**
 * APDU Protocol implementation for OTA firmware upgrade
 * Based on the Python reference implementation in OTA_Flash_Tool.py
 * Simplified for 128-byte chunk transfer with device-side buffering
 */
class ApduProtocol {
    
    companion object {
        // Command constants from Python implementation
        const val RESET_MCU: Byte = 0xCA.toByte()
        const val FIRMWARE_ERASE: Byte = 0xCB.toByte()
        const val FIRMWARE_PROGRAM: Byte = 0xCC.toByte()
        const val FIRMWARE_READ_HEADER: Byte = 0xCD.toByte()
        
        // Flash address constants - Based on UWB_OTA_PLAN_INTRO.md
        const val APP_FIRMWARE_START_ADDRESS = 0x280000   // External Flash App firmware storage area
        const val SR150_FIRMWARE_START_ADDRESS = 0x300000 // External Flash SR150 firmware storage area
        
        // Flash parameters
        const val W25Q32JV_PAGE_SIZE = 256
        const val W25Q32JV_SECTOR_SIZE = 4096
        const val W25Q32JV_BLOCK_64K_SIZE = 65536  // 64KB block size
        
        // 128-byte chunk transfer constants
        const val FLASH_ALIGNED_CHUNK_SIZE = 128  // 128 bytes per transfer
        const val FLASH_BUFFER_SIZE = 1024        // 1KB device buffer (4 pages)
        const val CHUNKS_PER_BUFFER = FLASH_BUFFER_SIZE / FLASH_ALIGNED_CHUNK_SIZE  // 8 chunks per buffer
        
        // Protocol constants
        const val PROTOCOL_HEADER_1: Byte = 0x00
        const val PROTOCOL_HEADER_2: Byte = 0x00
        const val PROTOCOL_HEADER_3: Byte = 0xFF.toByte()
        const val PROTOCOL_END: Byte = 0x00
        
        // APDU Payload structure constants (from ApduManagement.h)
        const val SADDR_SIZE = 6
        const val TADDR_SIZE = 6
        const val SNQ_SIZE = 1
        const val CMD_TYPE_SIZE = 1
        const val RESULT_SIZE = 1
        const val APDU_COUNT_SIZE = 1
        
        // Fixed SADDR and TADDR values (from Python implementation)
        private val SADDR = byteArrayOf(0x05, 0xFF.toByte(), 0xFF.toByte(), 0xFF.toByte(), 0xFF.toByte(), 0xFF.toByte())
        private val TADDR = byteArrayOf(0x06, 0xFF.toByte(), 0xFF.toByte(), 0xFF.toByte(), 0xFF.toByte(), 0xFF.toByte())
        private const val SNQ: Byte = 0x01
    }
    
    /**
     * Build protocol packet according to APDU format
     * @param command Command type (RESET_MCU, FIRMWARE_ERASE, FIRMWARE_PROGRAM, FIRMWARE_READ_HEADER)
     * @param address Target address (for erase/program/read operations)
     * @param data Data payload (for program operations) - 128 bytes for firmware chunks
     * @param blockCount Block count (for erase operations)
     * @param pages Pages count (for program operations) - calculated from data length
     * @param pageNumber Page number for packet loss detection (0-65535)
     * @return Complete protocol packet ready to send
     */
    fun buildProtocolPacket(
        command: Byte,
        address: Int = 0,
        data: ByteArray = byteArrayOf(),
        blockCount: Int = 1,
        pages: Int = 1,
        pageNumber: Int = 0
    ): ByteArray {
        val packet = mutableListOf<Byte>()
        
        // Add protocol header
        packet.add(PROTOCOL_HEADER_1)
        packet.add(PROTOCOL_HEADER_2)
        packet.add(PROTOCOL_HEADER_3)
        
        // Build payload
        val payload = mutableListOf<Byte>()
        
        // Add SADDR (6 bytes)
        payload.addAll(SADDR.toList())
        
        // Add TADDR (6 bytes)
        payload.addAll(TADDR.toList())
        
        // Add SNQ (1 byte)
        payload.add(SNQ)
        
        // Add command type (1 byte)
        payload.add(command)
        
        // Add result field (1 byte) - use for page number low byte
        payload.add((pageNumber and 0xFF).toByte())
        
        // Add apdu_count field (1 byte) - use for page number high byte
        payload.add(((pageNumber shr 8) and 0xFF).toByte())
        
        // Add command-specific data
        when (command) {
            RESET_MCU -> {
                // No additional data for reset command
            }
            
            FIRMWARE_ERASE -> {
                // Add address (4 bytes, little-endian)
                val addressBytes = intToLittleEndianBytes(address)
                payload.addAll(addressBytes.toList())
                
                // Add block count (1 byte)
                payload.add(blockCount.toByte())
            }
            
            FIRMWARE_PROGRAM -> {
                // Add address (4 bytes, little-endian)
                val addressBytes = intToLittleEndianBytes(address)
                payload.addAll(addressBytes.toList())
                
                // Add pages field (1 byte) - calculated from data length
                payload.add(pages.toByte())
                
                // Add actual firmware data (128 bytes)
                if (data.isNotEmpty()) {
                    payload.addAll(data.toList())
                }
            }
            
            FIRMWARE_READ_HEADER -> {
                // Add address (4 bytes, little-endian)
                val addressBytes = intToLittleEndianBytes(address)
                payload.addAll(addressBytes.toList())
            }
        }
        
        // Add payload length (2 bytes, little-endian)
        val payloadLength = payload.size
        val lengthBytes = shortToLittleEndianBytes(payloadLength.toShort())
        packet.addAll(lengthBytes.toList())
        
        // Add payload
        packet.addAll(payload)
        
        // Calculate and add DCS (Data Check Sum)
        var dcs = 0
        for (b in payload) {
            dcs += b.toInt() and 0xFF
        }
        dcs = (0x00 - dcs) and 0xFF
        packet.add(dcs.toByte())
        
        // Add protocol end
        packet.add(PROTOCOL_END)
        
        return packet.toByteArray()
    }
    
    /**
     * Parse response packet (for future use when device responses are implemented)
     * @param responseData Raw response data from device
     * @return Parsed response information
     */
    fun parseResponse(responseData: ByteArray): ApduResponse? {
        if (responseData.size < 5) {
            return null
        }
        
        // Verify protocol header
        if (responseData[0] != PROTOCOL_HEADER_1 || 
            responseData[1] != PROTOCOL_HEADER_2 || 
            responseData[2] != PROTOCOL_HEADER_3) {
            return null
        }
        
        // Extract payload length
        val payloadLength = ((responseData[4].toInt() and 0xFF) shl 8) or 
                           (responseData[3].toInt() and 0xFF)
        
        val expectedTotalLength = 5 + payloadLength + 2 // header(3) + length(2) + payload + DCS(1) + end(1)
        
        if (responseData.size < expectedTotalLength) {
            return null
        }
        
        // Verify end byte
        if (responseData[expectedTotalLength - 1] != PROTOCOL_END) {
            return null
        }
        
        // Extract payload
        val payloadStart = 5
        val payloadEnd = payloadStart + payloadLength
        val payload = responseData.sliceArray(payloadStart until payloadEnd)
        
        // Verify DCS
        val dcsPos = payloadEnd
        var calculatedSum = 0
        for (i in payloadStart until payloadEnd) {
            calculatedSum += responseData[i].toInt() and 0xFF
        }
        calculatedSum += responseData[dcsPos].toInt() and 0xFF
        calculatedSum = calculatedSum and 0xFF
        
        if (calculatedSum != 0) {
            return null // DCS verification failed
        }
        
        // Parse payload fields (according to ApduPayload_t structure)
        if (payload.size >= 16) {
            val cmdType = payload[13]
            val result = payload[14]
            
            return ApduResponse(
                cmdType = cmdType,
                result = result,
                payload = payload
            )
        }
        
        return null
    }
    
    /**
     * Convert integer to little-endian byte array (4 bytes)
     */
    private fun intToLittleEndianBytes(value: Int): ByteArray {
        return ByteBuffer.allocate(4)
            .order(ByteOrder.LITTLE_ENDIAN)
            .putInt(value)
            .array()
    }
    
    /**
     * Convert short to little-endian byte array (2 bytes)
     */
    private fun shortToLittleEndianBytes(value: Short): ByteArray {
        return ByteBuffer.allocate(2)
            .order(ByteOrder.LITTLE_ENDIAN)
            .putShort(value)
            .array()
    }
    

    
    /**
     * Calculate sectors needed for given data size
     */
    fun calculateSectorsNeeded(dataSize: Int): Int {
        return (dataSize + W25Q32JV_SECTOR_SIZE - 1) / W25Q32JV_SECTOR_SIZE
    }
    
    /**
     * Calculate 64KB blocks needed for given data size
     */
    fun calculateBlocksNeeded(dataSize: Int): Int {
        return (dataSize + W25Q32JV_BLOCK_64K_SIZE - 1) / W25Q32JV_BLOCK_64K_SIZE
    }
    
    /**
     * Split firmware data into 128-byte chunks for transmission
     * Ensures total chunk count is a multiple of 8 for device-side buffering
     * @param firmwareData Firmware data to split
     * @return List of 128-byte firmware chunks (count is multiple of 8)
     */
    fun splitFirmwareData(firmwareData: ByteArray): List<ByteArray> {
        val chunks = mutableListOf<ByteArray>()
        var offset = 0
        
        // Split firmware data into 128-byte chunks
        while (offset < firmwareData.size) {
            val remainingSize = firmwareData.size - offset
            val currentChunkSize = minOf(remainingSize, FLASH_ALIGNED_CHUNK_SIZE)
            
            val chunk = firmwareData.sliceArray(offset until offset + currentChunkSize)
            
            // Pad chunk to 128 bytes if necessary (last chunk)
            val paddedChunk = if (chunk.size < FLASH_ALIGNED_CHUNK_SIZE) {
                val paddingSize = FLASH_ALIGNED_CHUNK_SIZE - chunk.size
                chunk + ByteArray(paddingSize) { 0xFF.toByte() }
            } else {
                chunk
            }
            
            chunks.add(paddedChunk)
            offset += currentChunkSize
        }
        
        val originalChunkCount = chunks.size
        
        // Ensure chunk count is multiple of 8 for device-side buffering
        // Device writes to flash every 8 chunks (8 * 128 = 1024 bytes)
        val remainder = chunks.size % CHUNKS_PER_BUFFER
        if (remainder != 0) {
            val paddingChunksNeeded = CHUNKS_PER_BUFFER - remainder
            
            // Add padding chunks filled with 0xFF (erased flash state)
            repeat(paddingChunksNeeded) {
                val paddingChunk = ByteArray(FLASH_ALIGNED_CHUNK_SIZE) { 0xFF.toByte() }
                chunks.add(paddingChunk)
            }
        }
        return chunks
    }
    
    /**
     * Calculate checksum for payload data
     */
    private fun calculateChecksum(data: ByteArray): Int {
        var sum = 0
        for (b in data) {
            sum += b.toInt() and 0xFF
        }
        return (0x00 - sum) and 0xFF
    }
}

/**
 * Firmware type enumeration
 */
enum class FirmwareType(val startAddress: Int, val displayName: String) {
    APP_FIRMWARE(ApduProtocol.APP_FIRMWARE_START_ADDRESS, "App Firmware"),
    SR150_FIRMWARE(ApduProtocol.SR150_FIRMWARE_START_ADDRESS, "SR150 Firmware")
}

/**
 * Data class for APDU response
 */
data class ApduResponse(
    val cmdType: Byte,
    val result: Byte,
    val payload: ByteArray
) {
    val isSuccess: Boolean
        get() = result == 0x00.toByte()
    
    val commandName: String
        get() = when (cmdType) {
            ApduProtocol.RESET_MCU -> "Reset MCU"
            ApduProtocol.FIRMWARE_ERASE -> "Firmware Erase"
            ApduProtocol.FIRMWARE_PROGRAM -> "Firmware Program"
            ApduProtocol.FIRMWARE_READ_HEADER -> "Firmware Read Header"
            else -> "Unknown Command"
        }
    
    override fun equals(other: Any?): Boolean {
        if (this === other) return true
        if (javaClass != other?.javaClass) return false
        
        other as ApduResponse
        
        if (cmdType != other.cmdType) return false
        if (result != other.result) return false
        if (!payload.contentEquals(other.payload)) return false
        
        return true
    }
    
    override fun hashCode(): Int {
        var result1 = cmdType.toInt()
        result1 = 31 * result1 + result.toInt()
        result1 = 31 * result1 + payload.contentHashCode()
        return result1
    }
}