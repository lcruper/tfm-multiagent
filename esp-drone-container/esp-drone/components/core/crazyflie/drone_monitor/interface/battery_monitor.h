#ifndef BATTERY_MONITOR_H
#define BATTERY_MONITOR_H

#ifdef __cplusplus
extern "C" {
#endif

/**
 * @brief Starts the battery and motors monitoring task.
 * 
 * The task prints every MONITOR_DELAY_MS the battery voltage,
 * its state, and the PWM values and voltage of the motors.
 */
void startBatteryMonitor(void);

#ifdef __cplusplus
}
#endif

#endif // BATTERY_MONITOR_H
