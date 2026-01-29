package com.example.uwbota

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.Toast
import androidx.fragment.app.Fragment
import com.example.uwbota.ble.BleManager
import com.example.uwbota.databinding.FragmentDebugBinding
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

class DebugFragment : Fragment() {
    private var _binding: FragmentDebugBinding? = null
    private val binding get() = _binding!!

    override fun onCreateView(
        inflater: LayoutInflater,
        container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View {
        _binding = FragmentDebugBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        setupListeners()
    }

    private fun setupListeners() {
        // Q Value (Range 0-200, Default 50)
        binding.sliderQ.value = 50f
        binding.tvQValue.text = "50"
        binding.sliderQ.addOnChangeListener { _, value, _ ->
            binding.tvQValue.text = value.toInt().toString()
        }
        binding.btnSetQ.setOnClickListener {
            // Type 0x01 for Q
            sendValue(0x01.toByte(), binding.sliderQ.value.toInt().toByte())
        }

        // R Value (Range 0-200, Default 100)
        binding.sliderR.value = 100f
        binding.tvRValue.text = "100"
        binding.sliderR.addOnChangeListener { _, value, _ ->
            binding.tvRValue.text = value.toInt().toString()
        }
        binding.btnSetR.setOnClickListener {
            // Type 0x02 for R
            sendValue(0x02.toByte(), binding.sliderR.value.toInt().toByte())
        }

        // RED Value (Range 0-100, Default 45)
        binding.sliderRed.value = 45f
        binding.tvRedValue.text = "45"
        binding.sliderRed.addOnChangeListener { _, value, _ ->
            binding.tvRedValue.text = value.toInt().toString()
        }
        binding.btnSetRed.setOnClickListener {
            // Type 0x03 for RED
            sendValue(0x03.toByte(), binding.sliderRed.value.toInt().toByte())
        }
    }

    private fun sendValue(type: Byte, value: Byte) {
        val mainActivity = requireActivity() as? MainActivity
        if (mainActivity == null) return
        
        val bleManager = mainActivity.bleManager
        if (!bleManager.isConnected()) {
            Toast.makeText(context, "Bluetooth not connected", Toast.LENGTH_SHORT).show()
            return
        }

        // Protocol: A5 + type + value + 5A
        val packet = byteArrayOf(0xA5.toByte(), type, value, 0x5A.toByte())
        
        // Use a coroutine to send
        CoroutineScope(Dispatchers.IO).launch {
            val success = bleManager.sendApduFrame(packet)
            withContext(Dispatchers.Main) {
                if (success) {
                    binding.tvDebugStatus.text = "Sent: Type=${type}, Value=${value.toUByte()}"
                    Toast.makeText(context, "Sent successfully", Toast.LENGTH_SHORT).show()
                } else {
                    binding.tvDebugStatus.text = "Send failed"
                    Toast.makeText(context, "Send failed", Toast.LENGTH_SHORT).show()
                }
            }
        }
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }
}
