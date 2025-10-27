#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include <stdio.h>
#include "motors.h"
#include "pm_esplane.h"

#define MONITOR_DELAY_MS 500 

static void droneMonitorTask(void *param)
{
    while (1)
    {
        // Voltage
        float vbatt = pmGetBatteryVoltage();
        float vbattMin = pmGetBatteryVoltageMin();
        float vbattMax = pmGetBatteryVoltageMax();
        PMStates state = pmUpdateState();

        const char *stateStr;
        switch (state) {
            case charged:   stateStr = "CHARGED"; break;
            case charging:  stateStr = "CHARGING"; break;
            case lowPower:  stateStr = "LOW_POWER"; break;
            case battery:   stateStr = "BATTERY"; break;
            default:        stateStr = "UNKNOWN"; break;
        }

        printf("\n[DRONE MONITOR]-----------------------------\n");
        printf("Battery: %.2fV (Min: %.2fV Max: %.2fV) | State: %s\n", vbatt, vbattMin, vbattMax, stateStr);

        // Motors
        printf("[Motors] ");
        for (int i = 0; i < NBR_OF_MOTORS; i++)
        {
            int pwm = motorsGetRatio(i); 
            float vmotor = vbatt * ((float)pwm / 65535.0f); 
            printf("M%d: PWM=%d V=%.2fV\t", i+1, pwm, vmotor);
        }
        printf("\n");

        printf("-------------------------------------------\n");

        vTaskDelay(pdMS_TO_TICKS(MONITOR_DELAY_MS));
    }
}

void startDroneMonitor(void)
{
    xTaskCreate(droneMonitorTask, "DRONE_MONITOR", 4096, NULL, 1, NULL);
}
