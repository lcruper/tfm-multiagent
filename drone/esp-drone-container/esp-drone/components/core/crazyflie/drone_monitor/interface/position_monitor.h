#pragma once

/**
 * @brief Starts the drone position monitoring task.
 * 
 * The task prints and send by Wifi every MONITOR_DELAY_MS the drone's current
 * position and velocity.
 */
void startPositionMonitor(void);
