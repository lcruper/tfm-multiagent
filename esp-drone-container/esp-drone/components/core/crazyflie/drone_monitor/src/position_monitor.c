#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include <stdio.h>
#include "stabilizer.h"
#include "position_monitor.h"
#include "crtp.h"

#define POSITION_MONITOR_DELAY_MS 500
#define PORT_POSITION 11

extern state_t state;

static void sendPositionCRTP(float x, float y, float z, float roll, float pitch, float yaw)
{
    CRTPPacket p;
    p.port = PORT_POSITION;

    int n = snprintf((char*)p.data, CRTP_MAX_DATA_SIZE,
                     "X:%.2f Y:%.2f Z:%.2f R:%.2f P:%.2f Y:%.2f",
                     x, y, z, roll, pitch, yaw);

    p.size = (n > CRTP_MAX_DATA_SIZE) ? CRTP_MAX_DATA_SIZE : n;

    crtpSendPacket(&p);
}

static void positionMonitorTask(void *param)
{
    crtpInitTaskQueue(PORT_POSITION);

    while (1)
    {
        const state_t* s = stabilizerGetState();

        // Position
        float x = s->position.x;
        float y = s->position.y;
        float z = -s->position.z;

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

        sendPositionCRTP(x, y, z, roll, pitch, yaw);
        
        vTaskDelay(pdMS_TO_TICKS(POSITION_MONITOR_DELAY_MS));
    }
}

void startPositionMonitor(void)
{
    xTaskCreate(positionMonitorTask, "POSITION_MONITOR", 4096, NULL, 1, NULL);
}
