#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include <stdio.h>
#include <string.h>
#include "motors.h"
#include "pm_esplane.h"
#include "battery_monitor.h"
#include "wifi_esp32.h"

#define BATTERY_MONITOR_DELAY_MS 2000
#define PACKET_ID_BATTERY  0x01

typedef struct __attribute__((packed)){
    float vbatt;
    float vbattMin;
    float vbattMax;
    uint8_t state;
    float vmotor[NBR_OF_MOTORS];
} BatteryMotorPacket;

static void sendBatteryMotorUDP(float vbatt, float vbattMin, float vbattMax, PMStates state)
{
    BatteryMotorPacket packet;
    packet.vbatt = vbatt;
    packet.vbattMin = vbattMin;
    packet.vbattMax = vbattMax;
    packet.state = (uint8_t)state;

    for (int i = 0; i < NBR_OF_MOTORS; i++)
    {
        packet.vmotor[i] = vbatt * ((float)motorsGetRatio(i) / 65535.0f);
    }

    uint8_t buf[sizeof(BatteryMotorPacket)+1];
    buf[0] = PACKET_ID_BATTERY;            
    memcpy(buf+1, &packet, sizeof(BatteryMotorPacket));

    wifiSendData(sizeof(buf), buf);
}

static void batteryMonitorTask(void *param)
{
    while (1)
    {
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

        printf("[BATTERY]  V=%.2f (Min=%.2f Max=%.2f) | State=%s |\t",
               vbatt, vbattMin, vbattMax, stateStr);
        for (int i = 0; i < NBR_OF_MOTORS; i++)
        {
            float vmotor = vbatt * ((float)motorsGetRatio(i) / 65535.0f);
            printf("M%d=%.2f\t", i+1, vmotor);
        }
        printf("\n");
        sendBatteryMotorUDP(vbatt, vbattMin, vbattMax, state);

        vTaskDelay(pdMS_TO_TICKS(BATTERY_MONITOR_DELAY_MS));
    }
}

void startBatteryMonitor(void)
{
    xTaskCreate(batteryMonitorTask, "BATTERY_MONITOR", 4096, NULL, 1, NULL);
}
