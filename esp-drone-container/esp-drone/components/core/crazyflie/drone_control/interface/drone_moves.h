#pragma once
#include <stdbool.h>

/**
 * @brief Makes the drone hover in place, maintaining its current position and altitude.
 */
void droneHover(void);

/**
 * @brief Moves the drone vertically.
 * 
 * @param thrust Positive values make the drone ascend, negative values descend.
 */
void droneMoveVertical(float thrust);

/**
 * @brief Moves the drone horizontally in the XY plane.
 * 
 * @param vx Velocity along the X-axis (forward/backward).
 * @param vy Velocity along the Y-axis (left/right).
 */
void droneMoveXY(float vx, float vy);

/**
 * @brief Rotates the drone around its vertical axis (yaw).
 * 
 * @param yawRate Positive values rotate clockwise, negative counter-clockwise.
 */
void droneRotate(float yawRate);
