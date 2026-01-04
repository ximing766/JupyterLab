// Copyright (C) 2025
// Direction estimator native C API
// Exposes a small C interface for RSSI-based angle estimation

#pragma once

#if defined(_WIN32)
#  define RSIIDIR_API __declspec(dllexport)
#elif defined(__GNUC__)
#  define RSIIDIR_API __attribute__((visibility("default")))
#else
#  define RSIIDIR_API
#endif

#ifdef __cplusplus
extern "C" {
#endif

RSIIDIR_API void  de_reset_history(void);
// Estimate angle with built-in hysteresis and smoothing
RSIIDIR_API float de_estimate_angle(float rssi_a, float rssi_b, float dist_cm);

RSIIDIR_API int   de_selftest(float* out_angles, float* out_dists, int max_items);

// AA 55 | cmd | len | data... | checksum
RSIIDIR_API int   uart_build_frame(unsigned char cmd,
                                   const unsigned char* data,
                                   unsigned int len,
                                   unsigned char* out_buf,
                                   unsigned int out_size);

RSIIDIR_API int   uart_send_frame(const char* tty_path,
                                  int baud,
                                  const unsigned char* frame,
                                  unsigned int frame_len);

// Simplified UART API:
// 1) Send a fixed command by type (start/stop/clear/reboot/ota/version)
//    type uses protocol cmd values: 0x01,0x02,0x04,0x05,0x10,0x20
RSIIDIR_API int   uart_send_cmd(const char* tty_path, int baud, int type);
// 2) Set filter IDs (0x03)
RSIIDIR_API int   uart_set_filter(const char* tty_path, int baud,
                                  const unsigned char* ids, unsigned int count);

#ifdef __cplusplus
}
#endif
