package com.example.uwbota

import android.Manifest
import android.content.pm.PackageManager
import android.os.Build
import android.os.Bundle
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat
import androidx.core.view.WindowCompat
import androidx.core.view.WindowInsetsCompat
import androidx.fragment.app.Fragment
import com.example.uwbota.ble.BleManager
import com.example.uwbota.databinding.ActivityMainBinding
import com.example.uwbota.utils.LogManager

class MainActivity : AppCompatActivity() {
    private lateinit var binding: ActivityMainBinding
    lateinit var bleManager: BleManager // Public for Fragments

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        
        // Enable edge-to-edge display for modern look
        WindowCompat.setDecorFitsSystemWindows(window, false)
        
        binding = ActivityMainBinding.inflate(layoutInflater)
        setContentView(binding.root)
        
        setupEdgeToEdge()
        
        // Initialize BLE Manager
        bleManager = BleManager(this)
        
        checkPermissions()
        
        setupNavigation()
    }
    
    private fun setupEdgeToEdge() {
        binding.root.setOnApplyWindowInsetsListener { view, insets ->
            val systemBars = insets.getInsets(WindowInsetsCompat.Type.systemBars())
            view.setPadding(
                systemBars.left,
                systemBars.top,
                systemBars.right,
                0
            )
            insets
        }
    }
    
    private fun setupNavigation() {
        val homeFragment = HomeFragment()
        val debugFragment = DebugFragment()
        var activeFragment: Fragment = homeFragment
        
        // Add fragments initially
        supportFragmentManager.beginTransaction()
            .add(R.id.nav_host_fragment, homeFragment, "HOME")
            .add(R.id.nav_host_fragment, debugFragment, "DEBUG")
            .hide(debugFragment)
            .commit()
        
        binding.bottomNavigation.setOnItemSelectedListener { item ->
            when (item.itemId) {
                R.id.navigation_home -> {
                    supportFragmentManager.beginTransaction()
                        .hide(activeFragment)
                        .show(homeFragment)
                        .commit()
                    activeFragment = homeFragment
                    true
                }
                R.id.navigation_debug -> {
                    supportFragmentManager.beginTransaction()
                        .hide(activeFragment)
                        .show(debugFragment)
                        .commit()
                    activeFragment = debugFragment
                    true
                }
                else -> false
            }
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
