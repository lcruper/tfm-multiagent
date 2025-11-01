#include "drone_routines.h"
#include "drone_moves.h"
#include "FreeRTOS.h"
#include "task.h"


static void takeOffRoutineTask(void *param)
{
    printf("Take off routine started!\n");
    for (float t = 0.0f; t <= 0.5f; t += 0.05f) {
        droneMoveVertical(t);
        vTaskDelay(pdMS_TO_TICKS(200));
    }
    droneHover();
    vTaskDelete(NULL); 
}

static void landingRoutineTask(void *param)
{
    printf("Landing routine started!\n");
    for (float t = 0.5f; t >= 0.0f; t -= 0.05f) {
        droneMoveVertical(t);
        vTaskDelay(pdMS_TO_TICKS(200));
    }
    vTaskDelete(NULL);
}

static void squareFlightRoutineTask(void *param)
{
    printf("Square flight routine started!\n");
    takeOffRoutineTask(NULL);

    float sideDuration = 2000; 
    for (int i = 0; i < 4; i++) {
        switch(i) {
            case 0: droneMoveXY(0.5f, 0.0f); break;
            case 1: droneMoveXY(0.0f, 0.5f); break;
            case 2: droneMoveXY(-0.5f, 0.0f); break;
            case 3: droneMoveXY(0.0f, -0.5f); break;
        }
        vTaskDelay(pdMS_TO_TICKS(sideDuration));
        droneHover();
        vTaskDelay(pdMS_TO_TICKS(500));
    }

    landingRoutineTask(NULL);
    vTaskDelete(NULL);
}

static void rotateRoutineTask(void *param)
{
    printf("Rotate routine started!\n");
    takeOffRoutineTask(NULL);

    for (int i = 0; i < 8; i++) {
        droneRotate(45.0f);
        vTaskDelay(pdMS_TO_TICKS(500));
        droneHover();
    }

    landingRoutineTask(NULL);
    vTaskDelete(NULL);
}

void takeOffRoutine(void)
{
    xTaskCreate(takeOffRoutineTask, "TakeOffRoutine", 2048, NULL, 5, NULL);
}

void landingRoutine(void)
{
    xTaskCreate(landingRoutineTask, "LandingRoutine", 2048, NULL, 5, NULL);
}

void squareFlightRoutine(void)
{
    xTaskCreate(squareFlightRoutineTask, "SquareFlightRoutine", 4096, NULL, 5, NULL);
}

void rotateRoutine(void)
{
    xTaskCreate(rotateRoutineTask, "RotateRoutine", 2048, NULL, 5, NULL);
}

