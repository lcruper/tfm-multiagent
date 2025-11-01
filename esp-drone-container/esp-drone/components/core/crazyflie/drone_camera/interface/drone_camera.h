#ifndef DRONE_CAMERA_H
#define DRONE_CAMERA_H

#ifdef __cplusplus
extern "C" {
#endif

#include "esp_err.h"


/**
 * @brief Initializes the camera and configures pins and parameters.
 */
esp_err_t camera_init(void);

/**
 * @brief Captures a single frame from the camera.
 */
esp_err_t camera_capture(void);

/**
 * @brief Starts the camera capturing task.
 *
 * The task captures images every CAMERA_TASK_DELAY_MS.
 */
void startCapturingCamera(void);

#ifdef __cplusplus
}
#endif

#endif // DRONE_CAMERA_H
