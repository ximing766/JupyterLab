package com.example.uwbota.ui

import android.app.Dialog
import android.bluetooth.BluetoothDevice
import android.content.Context
import android.os.Bundle
import android.view.LayoutInflater
import androidx.recyclerview.widget.LinearLayoutManager
import com.example.uwbota.ble.BleManager
import com.example.uwbota.databinding.DialogDeviceSelectionBinding

class DeviceSelectionDialog(
    context: Context,
    private val bleManager: BleManager,
    private val onDeviceSelected: (String) -> Unit
) : Dialog(context) {
    
    private lateinit var binding: DialogDeviceSelectionBinding
    private lateinit var deviceAdapter: DeviceAdapter
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = DialogDeviceSelectionBinding.inflate(LayoutInflater.from(context))
        setContentView(binding.root)
        
        setupRecyclerView()
        setupClickListeners()
        startScanning()
    }
    
    private fun setupRecyclerView() {
        deviceAdapter = DeviceAdapter { deviceAddress ->
            onDeviceSelected(deviceAddress)
            dismiss()
        }
        
        binding.recyclerViewDevices.apply {
            layoutManager = LinearLayoutManager(context)
            adapter = deviceAdapter
        }
    }
    
    private fun setupClickListeners() {
        binding.btnCancel.setOnClickListener {
            dismiss()
        }
        
        binding.btnRefresh.setOnClickListener {
            startScanning()
        }
    }
    
    private fun startScanning() {
        bleManager.startScanning { device, rssi ->
            deviceAdapter.addDevice(device, rssi)
        }
    }
    
    override fun dismiss() {
        bleManager.stopScanning()
        super.dismiss()
    }
}