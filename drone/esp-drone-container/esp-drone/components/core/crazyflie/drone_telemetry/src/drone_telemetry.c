// Include necessary headers
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include <stdio.h>
#include <string.h>
#include "motors.h"
#include "pm_esplane.h"
#include "stabilizer.h"
#include "wifi_esp32.h"
#include "drone_telemetry.h"

//======================================================================
//                                CONSTANTS
//======================================================================
// Interval between updates (in ms)
#define BATTERY_MONITOR_DELAY_MS    1000
#define POSITION_MONITOR_DELAY_MS   500

// Packet type identifier for packets
#define PACKET_ID_BATTERY           0x01
#define PACKET_ID_POSITION          0x02

#define TASK_STACK_SIZE             4096
#define TASK_PRIORITY               1

//======================================================================
//                                PACKETS
//======================================================================
// Battery Packet: contains drone battery
typedef struct __attribute__((packed)) {
    float vbatt; // Battery voltage (V)
} BatteryPacket;

// Position Packet: contains drone position + orientation
typedef struct __attribute__((packed)) {
    float x, y, z;           // Position (m)
    float roll, pitch, yaw;  // Orientation (deg)
} PositionPacket;

//======================================================================
//                               UDP SENDER
//======================================================================
// Builds the packet, prepends the packet ID, and sends using WiFi.
static void sendUDP(uint8_t packetID, const void* data, size_t size)
{
    if (!data || size == 0) return;
    
    // 1 byte header + packet struct
    uint8_t buf[size + 1];
    buf[0] = packetID;
    memcpy(buf + 1, data, size);

    wifiSendData(sizeof(buf), buf);
}

//======================================================================
//                                MONITORS
//======================================================================
// ----------------------- Battery Monitor -----------------------------
// Periodically reads battery state, prints battery and motors states, and
// sends UDP packets with battery.
static void batteryMonitorTask(void *param)
{
    while (1)
    {
        // Get current battery state
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

        // Print to console
        printf("[BATTERY]  V=%.2f (Min=%.2f Max=%.2f) | State=%s | ",
               vbatt, vbattMin, vbattMax, stateStr);
        for (int i = 0; i < NBR_OF_MOTORS; i++)
        {
            // Calculate motor voltage based on battery voltage and motor ratio
            float vmotor = vbatt * ((float)motorsGetRatio(i) / 65535.0f);
            printf("M%d=%.2f\t", i+1, vmotor);
        }
        printf("\n");

        // Build battery packet
        BatteryPacket packet = { vbatt };

        // Send UDP battery packet
        sendUDP(PACKET_ID_BATTERY, &packet, sizeof(packet));

        // Wait before next update
        vTaskDelay(pdMS_TO_TICKS(BATTERY_MONITOR_DELAY_MS));
    }
}

// ----------------------------- Position Monitor -----------------------------
// Periodically reads stabilizer state, prints position, and
// sends UDP packets with position.
//======================================================================
static void positionMonitorTask(void *param)
{
    while (1)
    {
        // Get current stabilizer state
        const state_t* s = stabilizerGetState();

        // Check if stabilizer state is valid
        if (!s) {
            printf("[ERROR] stabilizerGetState() returned NULL\n");
            vTaskDelay(pdMS_TO_TICKS(100));
            continue;
        }

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

        // Print to console
        printf("[POSITION] x=%.2f, y=%.2f, z=%.2f (m) | "
              "vx=%.2f, vy=%.2f, vz=%.2f (m/s) | "
              "ax=%.2f, ay=%.2f, az=%.2f (m/s²) | "
              "roll=%.2f, pitch=%.2f, yaw=%.2f (°)\n",
              x, y, z, vx, vy, vz, ax, ay, az, roll, pitch, yaw);

        // Build UDP position packet
        PositionPacket packet;
        packet.x = x;   packet.y = y;   packet.z = z;
        packet.roll = roll; packet.pitch = pitch; packet.yaw = yaw;

        // Send UDP position packet
        sendUDP(PACKET_ID_POSITION, &packet, sizeof(packet));

        // Wait before next update
        vTaskDelay(pdMS_TO_TICKS(POSITION_MONITOR_DELAY_MS));
    }
}

//======================================================================
//                    PUBLIC API — START TELEMETRY TASK
//======================================================================
void startTelemetry(void)
{
    xTaskCreate(batteryMonitorTask, "BATTERY_MONITOR", TASK_STACK_SIZE, NULL, TASK_PRIORITY, NULL);
    xTaskCreate(positionMonitorTask, "POSITION_MONITOR", TASK_STACK_SIZE, NULL, TASK_PRIORITY, NULL);
}
