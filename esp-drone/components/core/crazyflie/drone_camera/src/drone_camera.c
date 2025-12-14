#include "esp_camera.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_log.h"
#include "driver/ledc.h"
#include "driver/i2c.h"
#include "driver/gpio.h"

static const char* TAG = "DRONE_CAMERA";

#define CAM_PIN_PWDN    -1
#define CAM_PIN_RESET   18
#define CAM_PIN_XCLK    16

#define CAM_PIN_SIOD    -1
#define CAM_PIN_SIOC    -1

#define CAM_PIN_D0      33
#define CAM_PIN_D1      46
#define CAM_PIN_D2      45
#define CAM_PIN_D3      42
#define CAM_PIN_D4      21
#define CAM_PIN_D5      19
#define CAM_PIN_D6      17
#define CAM_PIN_D7      15

#define CAM_PIN_VSYNC   13
#define CAM_PIN_HREF    14
#define CAM_PIN_PCLK    20

#define CAMERA_TASK_DELAY_MS 1000
#define CAMERA_STACK 4096

static camera_config_t camera_config = {
    .pin_pwdn  = CAM_PIN_PWDN,
    .pin_reset = CAM_PIN_RESET,
    .pin_xclk = CAM_PIN_XCLK,
    .pin_sccb_sda = CAM_PIN_SIOD,
    .pin_sccb_scl = CAM_PIN_SIOC,
    .pin_d7 = CAM_PIN_D7,
    .pin_d6 = CAM_PIN_D6,
    .pin_d5 = CAM_PIN_D5,
    .pin_d4 = CAM_PIN_D4,
    .pin_d3 = CAM_PIN_D3,
    .pin_d2 = CAM_PIN_D2,
    .pin_d1 = CAM_PIN_D1,
    .pin_d0 = CAM_PIN_D0,
    .pin_vsync = CAM_PIN_VSYNC,
    .pin_href = CAM_PIN_HREF,
    .pin_pclk = CAM_PIN_PCLK,

    .xclk_freq_hz = 20000000, 
    .ledc_timer = LEDC_TIMER_0,
    .ledc_channel = LEDC_CHANNEL_0,
    .pixel_format = PIXFORMAT_JPEG,
    .frame_size = FRAMESIZE_QQVGA,
    .fb_count = 1,
    .grab_mode = CAMERA_GRAB_WHEN_EMPTY,

    .sccb_i2c_port = I2C_NUM_1,
};

static void camera_setup_xclk(void)
{
    ledc_timer_config_t ledc_timer = {
        .speed_mode       = LEDC_LOW_SPEED_MODE,
        .duty_resolution  = LEDC_TIMER_8_BIT,
        .timer_num        = LEDC_TIMER_0,
        .freq_hz          = camera_config.xclk_freq_hz,
        .clk_cfg          = LEDC_AUTO_CLK
    };
    ledc_timer_config(&ledc_timer);

    ledc_channel_config_t ledc_channel = {
        .speed_mode     = LEDC_LOW_SPEED_MODE,
        .channel        = LEDC_CHANNEL_0,
        .timer_sel      = LEDC_TIMER_0,
        .intr_type      = LEDC_INTR_DISABLE,
        .gpio_num       = CAM_PIN_XCLK,
        .duty           = 128,  
        .hpoint         = 0
    };
    ledc_channel_config(&ledc_channel);
}

esp_err_t camera_init(void)
{
    //camera_setup_xclk();
 
    esp_err_t err = esp_camera_init(&camera_config);
    if (err != ESP_OK) {
        ESP_LOGE(TAG, "Init camera error: %d", err);
        return err;
    }

    ESP_LOGI(TAG, "Camera initialized successfully");
    return ESP_OK;
}

esp_err_t camera_capture(void)
{
    camera_fb_t *fb = esp_camera_fb_get();
    if (!fb) {
        ESP_LOGE(TAG, "Capture image error");
        return ESP_FAIL;
    }
    ESP_LOGI(TAG, "Image captured, size: %d bytes", fb->len);

    esp_camera_fb_return(fb);
    return ESP_OK;
}

static void cameraTask(void *arg)
{
    while (1) {
        camera_capture();
        vTaskDelay(pdMS_TO_TICKS(CAMERA_TASK_DELAY_MS));
    }
}

void startCapturingCamera(void)
{
    if (camera_init() == ESP_OK) {
        xTaskCreate(cameraTask, "cameraTask", CAMERA_STACK, NULL, 5, NULL);
    }
}
