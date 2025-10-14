package com.example.uwbota.ui

import android.bluetooth.BluetoothDevice
import android.view.LayoutInflater
import android.view.ViewGroup
import androidx.recyclerview.widget.RecyclerView
import com.example.uwbota.databinding.ItemDeviceBinding

data class ScannedDevice(
    val device: BluetoothDevice,
    val rssi: Int
)

class DeviceAdapter(
    private val onDeviceClick: (String) -> Unit
) : RecyclerView.Adapter<DeviceAdapter.DeviceViewHolder>() {
    
    private val devices = mutableListOf<ScannedDevice>()
    
    fun addDevice(device: BluetoothDevice, rssi: Int) {
        // Check if device already exists
        val existingIndex = devices.indexOfFirst { it.device.address == device.address }
        if (existingIndex >= 0) {
            // Update existing device with new RSSI
            devices[existingIndex] = ScannedDevice(device, rssi)
            notifyItemChanged(existingIndex)
        } else {
            // Add new device
            devices.add(ScannedDevice(device, rssi))
            notifyItemInserted(devices.size - 1)
        }
    }
    
    fun clearDevices() {
        val size = devices.size
        devices.clear()
        notifyItemRangeRemoved(0, size)
    }
    
    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): DeviceViewHolder {
        val binding = ItemDeviceBinding.inflate(
            LayoutInflater.from(parent.context),
            parent,
            false
        )
        return DeviceViewHolder(binding)
    }
    
    override fun onBindViewHolder(holder: DeviceViewHolder, position: Int) {
        holder.bind(devices[position])
    }
    
    override fun getItemCount(): Int = devices.size
    
    inner class DeviceViewHolder(private val binding: ItemDeviceBinding) :
        RecyclerView.ViewHolder(binding.root) {
        
        fun bind(scannedDevice: ScannedDevice) {
            val device = scannedDevice.device
            
            try {
                binding.tvDeviceName.text = device.name ?: "Unknown Device"
            } catch (e: SecurityException) {
                binding.tvDeviceName.text = "Unknown Device"
            }
            
            binding.tvDeviceAddress.text = device.address
            binding.tvRssi.text = "${scannedDevice.rssi} dBm"
            
            binding.root.setOnClickListener {
                onDeviceClick(device.address)
            }
        }
    }
}