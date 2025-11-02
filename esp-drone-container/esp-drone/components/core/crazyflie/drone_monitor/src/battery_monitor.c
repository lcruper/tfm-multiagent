#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include <stdio.h>
#include "motors.h"
#include "pm_esplane.h"
#include "crtp.h"
#include "battery_monitor.h"

#define BATTERY_MONITOR_DELAY_MS 500
#define PORT_BATTERY 10

static void sendBatteryMotorData(float vbatt, float vbattMin, float vbattMax, PMStates state)
{
    CRTPPacket p;
    p.port = PORT_BATTERY;

    int offset = snprintf((char*)p.data, CRTP_MAX_DATA_SIZE,
                          "V:%.2f Min:%.2f Max:%.2f State:%d ",
                          vbatt, vbattMin, vbattMax, (int)state);

    for (int i = 0; i < NBR_OF_MOTORS && offset < CRTP_MAX_DATA_SIZE; i++)
    {
        int pwm = motorsGetRatio(i);
        float vmotor = vbatt * ((float)pwm / 65535.0f);
        offset += snprintf((char*)(p.data + offset), CRTP_MAX_DATA_SIZE - offset,
                           "M%d:PWM=%d V=%.2f ", i+1, pwm, vmotor);
    }

    p.size = (offset > CRTP_MAX_DATA_SIZE) ? CRTP_MAX_DATA_SIZE : offset;

    crtpSendPacket(&p);
}

static void batteryMonitorTask(void *param)
{
    crtpInitTaskQueue(PORT_BATTERY);

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

        printf("\n[BATTERY MONITOR] ========================================================\n");
        printf("Battery: %.2fV (Min: %.2fV Max: %.2fV) | State: %s\n",
             vbatt, vbattMin, vbattMax, stateStr);

        // Motors
        printf("[Motors] ");
        for (int i = 0; i < NBR_OF_MOTORS; i++)
        {
            int pwm = motorsGetRatio(i); 
            float vmotor = vbatt * ((float)pwm / 65535.0f); 
            printf("M%d: PWM=%d V=%.2fV\t", i+1, pwm, vmotor);
        }
        printf("\n");

        printf("==============================================================================\n");

        sendBatteryMotorData(vbatt, vbattMin, vbattMax, state);

        vTaskDelay(pdMS_TO_TICKS(BATTERY_MONITOR_DELAY_MS));
    }
}

void startBatteryMonitor(void)
{
    xTaskCreate(batteryMonitorTask, "BATTERY_MONITOR", 4096, NULL, 1, NULL);
}
