#include "drone_camera.h"
#include "esp_camera.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_log.h"

static const char* TAG = "DRONE_CAMERA";
#define CAMERA_TASK_DELAY_MS 1000  
#define CAMERA_STACK 2048

#define CAM_PIN_PWDN    -1
#define CAM_PIN_RESET   -1
#define CAM_PIN_XCLK    21
#define CAM_PIN_SIOD    26
#define CAM_PIN_SIOC    27
#define CAM_PIN_D7      35
#define CAM_PIN_D6      34
#define CAM_PIN_D5      39
#define CAM_PIN_D4      36
#define CAM_PIN_D3      19
#define CAM_PIN_D2      18
#define CAM_PIN_D1       5
#define CAM_PIN_D0       4
#define CAM_PIN_VSYNC   25
#define CAM_PIN_HREF    23
#define CAM_PIN_PCLK    22

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
    .pixel_format = PIXFORMAT_GRAYSCALE,  
    .frame_size = FRAMESIZE_QCIF,        
    .fb_count = 1,
    .grab_mode = CAMERA_GRAB_WHEN_EMPTY
};

esp_err_t camera_init(void){
    // Initialize the camera
    esp_err_t err = esp_camera_init(&camera_config);
    if (err != ESP_OK) {
        ESP_LOGE(TAG, "Camera Init Failed");
        return err;
    }
    ESP_LOGI(TAG, "Camera initialized");
    return ESP_OK;
}


esp_err_t camera_capture(void){ 
    // Acquire a frame 
    camera_fb_t *fb = esp_camera_fb_get(); 
    if (!fb) { 
        ESP_LOGE(TAG, "Camera Capture Failed"); 
        return ESP_FAIL; 
    } 
    // Return the frame buffer back to the driver for reuse 
    esp_camera_fb_return(fb);
    return ESP_OK; 
}


static void cameraTask(void *arg) {
    while(1) {
        if(camera_capture() == ESP_OK) {
            ESP_LOGI(TAG, "Image captured successfully");
        } else {
            ESP_LOGE(TAG, "Failed to capture image");
        }
        vTaskDelay(pdMS_TO_TICKS(CAMERA_TASK_DELAY_MS));
    }
}

void startCapturingCamera(void)
{
    xTaskCreate(cameraTask, "cameraTask", CAMERA_STACK, NULL, 5, NULL);
}
