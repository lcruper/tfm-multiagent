#pragma once
#include <stdbool.h>

/**
 * @brief Initializes the UART interface for communicating with the drone.
 */
void droneUartInit(void);

/**
 * @brief Starts the UART listening task to handle incoming commands.
 */
void startUART(void);