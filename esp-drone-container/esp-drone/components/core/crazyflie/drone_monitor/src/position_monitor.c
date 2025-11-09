#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include <stdio.h>
#include <string.h>
#include "stabilizer.h"
#include "position_monitor.h"
#include "wifi_esp32.h"

#define POSITION_MONITOR_DELAY_MS 500
#define PACKET_ID_POSITION 0x02

extern state_t state;

typedef struct __attribute__((packed)){
    float x;
    float y;
    float z;
    float vx;
    float vy;
    float vz;
    float roll;
    float pitch;
    float yaw;
} PositionPacket;

static void sendPositionUDP(float x, float y, float z,
                            float vx, float vy, float vz,
                            float roll, float pitch, float yaw)
{
    PositionPacket packet;
    packet.x = x;
    packet.y = y;
    packet.z = z;
    packet.vx = vx;
    packet.vy = vy;
    packet.vz = vz;
    packet.roll = roll;
    packet.pitch = pitch;
    packet.yaw = yaw;

    uint8_t buf[sizeof(PositionPacket)+1];
    buf[0] = PACKET_ID_POSITION;          
    memcpy(buf+1, &packet, sizeof(PositionPacket));

    wifiSendData(sizeof(buf), buf);
}

static void positionMonitorTask(void *param)
{
    while (1)
    {
        const state_t* s = stabilizerGetState();

        // Position
        float x = s->position.x;
        float y = s->position.y;
        float z = s->position.z;

        // Velocity
        float vx = s->velocity.x;
        float vy = s->velocity.y;
        float vz = s->velocity.z;

        // Orientation
        float roll  = s->attitude.roll;
        float pitch = s->attitude.pitch;
        float yaw   = s->attitude.yaw;

        printf("\n[POSITION MONITOR] ========================================================\n");
        printf("Position -> x: %.2f  y: %.2f  z: %.2f (m)\n", x, y, z);
        printf("Velocity -> x: %.2f  y: %.2f  z: %.2f (m/s)\n", vx, vy, vz);
        printf("Attitude -> Roll: %.2f°  Pitch: %.2f°  Yaw: %.2f°\n",
               roll, pitch, yaw);
        printf("==============================================================================\n");

        sendPositionUDP(x, y, z, vx, vy, vz, roll, pitch, yaw);
        
        vTaskDelay(pdMS_TO_TICKS(POSITION_MONITOR_DELAY_MS));
    }
}

void startPositionMonitor(void)
{
    xTaskCreate(positionMonitorTask, "POSITION_MONITOR", 4096, NULL, 1, NULL);
}
