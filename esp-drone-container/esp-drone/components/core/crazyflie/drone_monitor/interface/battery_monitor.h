#pragma once

/**
 * @brief Starts the battery and motors monitoring task.
 * 
 * The task prints every MONITOR_DELAY_MS the battery voltage,
 * its state, and the PWM values and voltage of the motors.
 */
void startBatteryMonitor(void);