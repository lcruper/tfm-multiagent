#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include <stdio.h>
#include <string.h>
#include "stabilizer.h"
#include "drone_alert.h"
#include "wifi_esp32.h"
#include <time.h>


#define ALERT_MONITOR_DELAY_MS 500
#define PACKET_ID_ALERT 0x03

extern state_t state;

typedef struct __attribute__((packed)){
    float x;
    float y;
} AlertPacket;

static void sendAlertUDP(float x, float y)
{
    AlertPacket packet;
    packet.x = x;
    packet.y = y;

    uint8_t buf[sizeof(AlertPacket)+1];
    buf[0] = PACKET_ID_ALERT;          
    memcpy(buf+1, &packet, sizeof(AlertPacket));

    wifiSendData(sizeof(buf), buf);
}

static void alertTask(void *param)
{
    srand((unsigned int)time(NULL));

    while (1)
    {
        const state_t* s = stabilizerGetState();
        if ((rand() % 100) < 10)
        {
            float x = s->position.x;
            float y = s->position.y;

            printf("[ALERT!] x=%.2f, y=%.2f\n", x, y);
            sendAlertUDP(x, y);
        }

        vTaskDelay(pdMS_TO_TICKS(ALERT_MONITOR_DELAY_MS));
    }
}

void startAlert(void)
{
    xTaskCreate(alertTask, "ALERT_TASK", 4096, NULL, 1, NULL);
}
