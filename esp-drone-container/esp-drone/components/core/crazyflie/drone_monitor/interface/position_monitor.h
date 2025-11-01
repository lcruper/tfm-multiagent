#ifndef POSITION_MONITOR_H
#define POSITION_MONITOR_H

#ifdef __cplusplus
extern "C" {
#endif

/**
 * @brief Starts the drone position monitoring task.
 * 
 * The task prints every MONITOR_DELAY_MS the drone's current
 * position and velocity.
 */
void startPositionMonitor(void);

#ifdef __cplusplus
}
#endif

#endif // POSITION_MONITOR_H
