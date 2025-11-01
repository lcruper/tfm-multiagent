#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include <stdio.h>
#include "stabilizer.h"
#include "position_monitor.h"

#define POSITION_MONITOR_DELAY_MS 500

extern state_t state;

static void positionMonitorTask(void *param)
{
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

        vTaskDelay(pdMS_TO_TICKS(POSITION_MONITOR_DELAY_MS));
    }
}

void startPositionMonitor(void)
{
    xTaskCreate(positionMonitorTask, "POSITION_MONITOR", 4096, NULL, 1, NULL);
}
