package com.example.uwbota

import java.nio.ByteBuffer
import java.nio.ByteOrder
import java.security.MessageDigest

/**
 * Firmware header structure for App firmware
 * Based on Python OTA tool specifications
 * Header format: magic(4) + version(4) + size(4) + crc32(4) + update_flag(1) + padding(3) + reserved(12) = 32 bytes
 */
data class FirmwareHeader(
    val magic: Int = FIRMWARE_MAGIC,
    val version: Int,
    val size: Int,
    val crc32: Int,
    val updateFlag: Byte = 1,
    val reserved: ByteArray = ByteArray(15) { 0 } // 3 bytes padding + 12 bytes reserved
) {
    companion object {
        const val FIRMWARE_MAGIC = 0x12345678 // Magic number matching Python OTA tool
        const val HEADER_SIZE = 32 // Total header size in bytes
        
        /**
         * Create firmware header from firmware data
         */
        fun createFromFirmware(firmwareData: ByteArray, version: Int): FirmwareHeader {
            val size = firmwareData.size
            val crc32 = calculateCRC32(firmwareData)
            
            return FirmwareHeader(
                version = version,
                size = size,
                crc32 = crc32
            )
        }
        
        /**
         * Parse firmware header from byte array
         */
        fun fromByteArray(data: ByteArray): FirmwareHeader? {
            if (data.size < HEADER_SIZE) return null
            
            val buffer = ByteBuffer.wrap(data).order(ByteOrder.LITTLE_ENDIAN)
            
            val magic = buffer.int
            if (magic != FIRMWARE_MAGIC) return null
            
            val version = buffer.int
            val size = buffer.int
            val crc32 = buffer.int
            val updateFlag = buffer.get()
            
            // Skip 3 bytes padding
            buffer.get() // skip padding byte 1
            buffer.get() // skip padding byte 2
            buffer.get() // skip padding byte 3
            
            // Read 12 bytes reserved data
            val reservedData = ByteArray(12)
            buffer.get(reservedData)
            
            // Create 15-byte reserved array (12 bytes data + 3 bytes padding already handled)
            val reserved = ByteArray(15)
            reservedData.copyInto(reserved, 0, 0, 12)
            
            return if (magic == FIRMWARE_MAGIC) {
                FirmwareHeader(magic, version, size, crc32, updateFlag, reserved)
            } else null
        }
        
        /**
         * Calculate CRC32 checksum for firmware data
         */
        private fun calculateCRC32(data: ByteArray): Int {
            val crc32Table = IntArray(256)
            
            // Initialize CRC32 table
            for (i in 0..255) {
                var crc = i
                for (j in 0..7) {
                    crc = if (crc and 1 != 0) {
                        (crc ushr 1) xor 0xEDB88320.toInt()
                    } else {
                        crc ushr 1
                    }
                }
                crc32Table[i] = crc
            }
            
            // Calculate CRC32
            var crc = 0xFFFFFFFF.toInt()
            for (byte in data) {
                val index = (crc xor byte.toInt()) and 0xFF
                crc = (crc ushr 8) xor crc32Table[index]
            }
            
            return crc xor 0xFFFFFFFF.toInt()
        }
    }
    
    /**
     * Convert header to byte array
     * Format: magic(4) + version(4) + size(4) + crc32(4) + updateFlag(1) + padding(3) + reserved(12)
     */
    fun toByteArray(): ByteArray {
        val buffer = ByteBuffer.allocate(HEADER_SIZE).order(ByteOrder.LITTLE_ENDIAN)
        buffer.putInt(magic)
        buffer.putInt(version)
        buffer.putInt(size)
        buffer.putInt(crc32)
        buffer.put(updateFlag)
        
        // Add 3 bytes padding to align to 4-byte boundary
        buffer.put(0.toByte())
        buffer.put(0.toByte())
        buffer.put(0.toByte())
        
        // Add 12 bytes reserved (first 12 bytes of reserved array)
        val reservedData = if (reserved.size >= 12) {
            reserved.copyOf(12)
        } else {
            ByteArray(12).also { reserved.copyInto(it, 0, 0, minOf(reserved.size, 12)) }
        }
        buffer.put(reservedData)
        
        return buffer.array()
    }
    
    /**
     * Verify firmware data against header
     */
    fun verifyFirmware(firmwareData: ByteArray): Boolean {
        if (firmwareData.size != size) return false
        
        val calculatedCrc = Companion.calculateCRC32(firmwareData)
        return calculatedCrc == crc32
    }
    
    /**
     * Get version string representation
     */
    fun getVersionString(): String {
        val major = (version shr 16) and 0xFFFF
        val minor = version and 0xFFFF
        return "v$major.$minor"
    }
    
    /**
     * Get formatted size string
     */
    fun getSizeString(): String {
        return when {
            size >= 1024 * 1024 -> String.format("%.2f MB", size / (1024.0 * 1024.0))
            size >= 1024 -> String.format("%.2f KB", size / 1024.0)
            else -> "$size bytes"
        }
    }
    
    override fun equals(other: Any?): Boolean {
        if (this === other) return true
        if (javaClass != other?.javaClass) return false
        
        other as FirmwareHeader
        
        if (magic != other.magic) return false
        if (version != other.version) return false
        if (size != other.size) return false
        if (crc32 != other.crc32) return false
        if (updateFlag != other.updateFlag) return false
        if (!reserved.contentEquals(other.reserved)) return false
        
        return true
    }
    
    override fun hashCode(): Int {
        var result = magic
        result = 31 * result + version
        result = 31 * result + size
        result = 31 * result + crc32
        result = 31 * result + updateFlag
        result = 31 * result + reserved.contentHashCode()
        return result
    }
}