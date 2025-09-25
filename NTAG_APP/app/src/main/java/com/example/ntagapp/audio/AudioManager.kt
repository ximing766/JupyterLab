package com.example.ntagapp.audio

import android.content.Context
import android.media.AudioAttributes
import android.media.MediaPlayer
import android.media.SoundPool
import android.net.Uri
import com.example.ntagapp.R
import com.example.ntagapp.model.GameResult

/**
 * Audio manager for handling game sounds and background music
 */
class AudioManager(private val context: Context) {
    
    private var soundPool: SoundPool? = null
    private var mediaPlayer: MediaPlayer? = null
    
    // Sound IDs
    private var clickSoundId: Int = 0
    private var winSoundId: Int = 0
    private var loseSoundId: Int = 0
    private var drawSoundId: Int = 0
    private var thinkingSoundId: Int = 0
    
    // Settings
    private var soundEnabled = true
    private var musicEnabled = true
    private var soundVolume = 1.0f
    private var musicVolume = 0.5f
    
    /**
     * Sound types enum
     */
    enum class SoundType {
        CLICK, WIN, LOSE, DRAW, THINKING
    }
    
    init {
        initializeSoundPool()
        loadSounds()
    }
    
    /**
     * Initialize SoundPool for short sound effects
     */
    private fun initializeSoundPool() {
        val audioAttributes = AudioAttributes.Builder()
            .setUsage(AudioAttributes.USAGE_GAME)
            .setContentType(AudioAttributes.CONTENT_TYPE_SONIFICATION)
            .build()
        
        soundPool = SoundPool.Builder()
            .setMaxStreams(5)
            .setAudioAttributes(audioAttributes)
            .build()
    }
    
    /**
     * Load sound files into SoundPool
     */
    private fun loadSounds() {
        soundPool?.let { pool ->
            // Load actual sound files from res/raw/
            clickSoundId = pool.load(context, R.raw.click_sound, 1)
            winSoundId = pool.load(context, R.raw.win_sound, 1)
            loseSoundId = pool.load(context, R.raw.lose_sound, 1)
            drawSoundId = pool.load(context, R.raw.draw_sound, 1)
            thinkingSoundId = pool.load(context, R.raw.thinking_sound, 1)
        }
    }
    
    /**
     * Play sound by type
     */
    fun playSound(soundType: SoundType) {
        if (!soundEnabled) return
        
        val soundId = when (soundType) {
            SoundType.CLICK -> clickSoundId
            SoundType.WIN -> winSoundId
            SoundType.LOSE -> loseSoundId
            SoundType.DRAW -> drawSoundId
            SoundType.THINKING -> thinkingSoundId
        }
        
        soundPool?.play(soundId, soundVolume, soundVolume, 1, 0, 1.0f)
    }
    
    /**
     * Play click sound
     */
    fun playClickSound() {
        playSound(SoundType.CLICK)
    }
    
    /**
     * Play thinking sound
     */
    fun playThinkingSound() {
        playSound(SoundType.THINKING)
    }
    
    /**
     * Play result sound based on game result
     */
    fun playResultSound(result: GameResult) {
        val soundType = when (result) {
            GameResult.WIN -> SoundType.WIN
            GameResult.LOSE -> SoundType.LOSE
            GameResult.DRAW -> SoundType.DRAW
        }
        playSound(soundType)
    }
    
    /**
     * Start background music
     */
    fun startBackgroundMusic() {
        if (!musicEnabled) return
        
        try {
            mediaPlayer?.release()
            mediaPlayer = MediaPlayer().apply {
                setDataSource(context, Uri.parse("android.resource://${context.packageName}/${R.raw.background_music}"))
                setVolume(musicVolume, musicVolume)
                isLooping = true
                prepareAsync()
                setOnPreparedListener { start() }
            }
        } catch (e: Exception) {
            // Handle error
            e.printStackTrace()
        }
    }
    
    /**
     * Stop background music
     */
    fun stopBackgroundMusic() {
        mediaPlayer?.let {
            if (it.isPlaying) {
                it.stop()
            }
        }
    }
    
    /**
     * Pause background music
     */
    fun pauseBackgroundMusic() {
        mediaPlayer?.let {
            if (it.isPlaying) {
                it.pause()
            }
        }
    }
    
    /**
     * Resume background music
     */
    fun resumeBackgroundMusic() {
        mediaPlayer?.let {
            if (!it.isPlaying) {
                it.start()
            }
        }
    }
    
    /**
     * Set sound enabled/disabled
     */
    fun setSoundEnabled(enabled: Boolean) {
        soundEnabled = enabled
    }
    
    /**
     * Set music enabled/disabled
     */
    fun setMusicEnabled(enabled: Boolean) {
        musicEnabled = enabled
        if (!enabled) {
            stopBackgroundMusic()
        } else {
            startBackgroundMusic()
        }
    }
    
    /**
     * Set sound volume (0.0 to 1.0)
     */
    fun setSoundVolume(volume: Float) {
        soundVolume = volume.coerceIn(0.0f, 1.0f)
    }
    
    /**
     * Set music volume (0.0 to 1.0)
     */
    fun setMusicVolume(volume: Float) {
        musicVolume = volume.coerceIn(0.0f, 1.0f)
        mediaPlayer?.setVolume(musicVolume, musicVolume)
    }
    
    /**
     * Release resources
     */
    fun release() {
        soundPool?.release()
        soundPool = null
        
        mediaPlayer?.release()
        mediaPlayer = null
    }
}