#include "drone_uart.h"
#include "driver/uart.h"
#include "esp_log.h"
#include "string.h"
#include "drone_routines.h"

#define UART_PORT_NUM      UART_NUM_0  
#define UART_BAUD_RATE     115200
#define BUF_SIZE           256

static const char *TAG = "DRONE_UART";

void droneUartInit(void)
{
    uart_config_t uart_config = {
        .baud_rate = UART_BAUD_RATE,
        .data_bits = UART_DATA_8_BITS,
        .parity    = UART_PARITY_DISABLE,
        .stop_bits = UART_STOP_BITS_1,
        .flow_ctrl = UART_HW_FLOWCTRL_DISABLE
    };

    uart_param_config(UART_PORT_NUM, &uart_config);
    uart_driver_install(UART_PORT_NUM, BUF_SIZE * 2, 0, 0, NULL, 0);

    ESP_LOGI(TAG, "UART initialized on port %d", UART_PORT_NUM);
}

static void droneUartTask(void *param)
{
    uint8_t data[BUF_SIZE];
    while (1)
    {
        int len = uart_read_bytes(UART_PORT_NUM, data, BUF_SIZE - 1, pdMS_TO_TICKS(100));
        if (len > 0)
        {
            data[len] = '\0';
            ESP_LOGI(TAG, "Received command: %s", (char*)data);

            if (strcmp((char*)data, "1") == 0) {
                takeOffRoutine();
            } else if (strcmp((char*)data, "2") == 0) {
                landingRoutine();
            } else if (strcmp((char*)data, "3") == 0) {
                squareFlightRoutine();
            } else if (strcmp((char*)data, "3") == 0) {
                rotateRoutine();
            } else {
                ESP_LOGW(TAG, "Unknown command");
            }
        }
        vTaskDelay(pdMS_TO_TICKS(100));
    }
}

void startUART(void) 
{
    xTaskCreate(droneUartTask, "DroneUartTask", 4096, NULL, 5, NULL);
}
