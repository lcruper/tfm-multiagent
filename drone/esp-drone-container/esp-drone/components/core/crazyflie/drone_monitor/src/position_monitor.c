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
    float roll;
    float pitch;
    float yaw;
} PositionPacket;

static void sendPositionUDP(float x, float y, float z,
                            float roll, float pitch, float yaw)
{
    PositionPacket packet;
    packet.x = x;
    packet.y = y;
    packet.z = z;
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

        // Acceleration
        float ax = s->acc.x;
        float ay = s->acc.y;
        float az = s->acc.z;

        // Orientation
        float roll  = s->attitude.roll;
        float pitch = s->attitude.pitch;
        float yaw   = s->attitude.yaw;

        printf("[POSITION] x=%.2f, y=%.2f, z=%.2f (m) | "
              "vx=%.2f, vy=%.2f, vz=%.2f (m/s) | "
              "ax=%.2f, ay=%.2f, az=%.2f (m/s²) | "
              "roll=%.2f, pitch=%.2f, yaw=%.2f (°)\n",
              x, y, z, vx, vy, vz, ax, ay, az, roll, pitch, yaw);

        sendPositionUDP(x, y, z, roll, pitch, yaw);
        
        vTaskDelay(pdMS_TO_TICKS(POSITION_MONITOR_DELAY_MS));
    }
}

void startPositionMonitor(void)
{
    xTaskCreate(positionMonitorTask, "POSITION_MONITOR", 4096, NULL, 1, NULL);
}
