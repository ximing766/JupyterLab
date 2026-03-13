package com.example.uwbota

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.Toast
import androidx.fragment.app.Fragment
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView
import com.example.uwbota.databinding.FragmentDebugBinding
import com.example.uwbota.databinding.ItemDebugParamBinding
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

class DebugFragment : Fragment() {
    private var _binding: FragmentDebugBinding? = null
    private val binding get() = _binding!!

    // Data class for debug parameters
    data class DebugParam(
        val id: Int,
        val name: String,
        val type: Byte,
        val min: Int,
        val max: Int,
        var value: Int
    )

    // List of parameters
    private val params = mutableListOf(
        DebugParam(1, "Vert Height", 0x01.toByte(), 50, 350, 250),
        DebugParam(2, "Horiz Offset", 0x02.toByte(), 50, 350, 100),
        DebugParam(3, "Trigger Dist", 0x03.toByte(), 50, 350, 200),
        DebugParam(4, "Q Value", 0x09.toByte(), 0, 200, 50),
        DebugParam(5, "R Value", 0x0A.toByte(), 0, 200, 100),
        DebugParam(6, "Reset", 0xF1.toByte(), 0, 0, 0),
        DebugParam(7, "Reserved 2", 0x05.toByte(), 0, 255, 0),
        DebugParam(8, "Reserved 3", 0x06.toByte(), 0, 255, 0),
        DebugParam(9, "Reserved 4", 0x07.toByte(), 0, 255, 0),
        DebugParam(10, "Reserved 5", 0x08.toByte(), 0, 255, 0),
        
    )

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
        setupRecyclerView()
    }

    private fun setupRecyclerView() {
        binding.rvDebugParams.layoutManager = LinearLayoutManager(context)
        binding.rvDebugParams.adapter = DebugParamAdapter(params)
    }

    private fun sendValue(type: Byte, value: Int) {
        val mainActivity = requireActivity() as? MainActivity
        if (mainActivity == null) return
        
        val bleManager = mainActivity.bleManager
        if (!bleManager.isConnected()) {
            Toast.makeText(context, "Bluetooth not connected", Toast.LENGTH_SHORT).show()
            return
        }

        val packet: ByteArray
        val valueStr: String

        if (value > 255) {
            // Send 2 bytes: High Byte, Low Byte (Big Endian)
            val high = (value shr 8).toByte()
            val low = (value and 0xFF).toByte()
            packet = byteArrayOf(0xA5.toByte(), type, high, low, 0x5A.toByte())
            valueStr = "0x%04X (%d)".format(value, value)
        } else {
            // Send 1 byte: Value
            packet = byteArrayOf(0xA5.toByte(), type, value.toByte(), 0x5A.toByte())
            valueStr = "0x%02X (%d)".format(value, value)
        }

        // Use a coroutine to send
        CoroutineScope(Dispatchers.IO).launch {
            val success = bleManager.sendApduFrame(packet)
            withContext(Dispatchers.Main) {
                if (success) {
                    // Using Toast as status textview is removed
                    // Toast.makeText(context, "Sent: $valueStr", Toast.LENGTH_SHORT).show()
                } else {
                    Toast.makeText(context, "Send failed", Toast.LENGTH_SHORT).show()
                }
            }
        }
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }

    // Inner Adapter Class
    inner class DebugParamAdapter(private val items: List<DebugParam>) : 
        RecyclerView.Adapter<DebugParamAdapter.ViewHolder>() {

        inner class ViewHolder(val itemBinding: ItemDebugParamBinding) : 
            RecyclerView.ViewHolder(itemBinding.root)

        override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): ViewHolder {
            val itemBinding = ItemDebugParamBinding.inflate(
                LayoutInflater.from(parent.context), 
                parent, 
                false
            )
            return ViewHolder(itemBinding)
        }

        override fun onBindViewHolder(holder: ViewHolder, position: Int) {
            val item = items[position]
            with(holder.itemBinding) {
                tvParamName.text = item.name
                
                // Handle Reset type (0xF1) separately
                if (item.type == 0xF1.toByte()) {
                    sliderParam.visibility = View.INVISIBLE
                    tvParamValue.visibility = View.INVISIBLE
                    sliderParam.isEnabled = false
                } else {
                    sliderParam.visibility = View.VISIBLE
                    tvParamValue.visibility = View.VISIBLE
                    sliderParam.isEnabled = true
                    
                    // Update slider range
                    sliderParam.valueFrom = item.min.toFloat()
                    sliderParam.valueTo = item.max.toFloat()
                    
                    // Ensure value is within range
                    if (item.value < item.min) item.value = item.min
                    if (item.value > item.max) item.value = item.max
                    
                    sliderParam.value = item.value.toFloat()
                    tvParamValue.text = item.value.toString()
                }

                // Slider listener
                sliderParam.clearOnChangeListeners()
                sliderParam.addOnChangeListener { _, value, _ ->
                    val intValue = value.toInt()
                    item.value = intValue
                    tvParamValue.text = intValue.toString()
                }

                // Button listener - Now using ImageButton for compact design
                btnSetParam.setOnClickListener {
                    sendValue(item.type, item.value)
                    Toast.makeText(context, "Sent ${item.name}: ${item.value}", Toast.LENGTH_SHORT).show()
                }
            }
        }

        override fun getItemCount() = items.size
    }
}
