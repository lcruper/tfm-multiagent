#include "drone_moves.h"
#include "commander.h"
#include "FreeRTOS.h"
#include "task.h"

void droneHover(void)
{
    setpoint_t sp = {0};
    sp.thrust = 0.5f;
    sp.mode.x = modeDisable;
    sp.mode.y = modeDisable;
    sp.mode.z = modeAbs;
    sp.mode.roll = modeAbs;
    sp.mode.pitch = modeAbs;
    sp.mode.yaw = modeVelocity;
    commanderSetSetpoint(&sp, 1);
}

void droneMoveVertical(float thrust)
{
    setpoint_t sp = {0};
    sp.thrust = 0.5f + thrust; 
    sp.mode.x = modeDisable;
    sp.mode.y = modeDisable;
    sp.mode.z = modeAbs;
    sp.mode.roll = modeAbs;
    sp.mode.pitch = modeAbs;
    sp.mode.yaw = modeVelocity;
    commanderSetSetpoint(&sp, 1);
}

void droneMoveXY(float vx, float vy)
{
    setpoint_t sp = {0};
    sp.velocity.x = vx; 
    sp.velocity.y = vy;  
    sp.mode.x = modeVelocity;
    sp.mode.y = modeVelocity;
    sp.mode.z = modeAbs;
    sp.mode.roll = modeAbs;
    sp.mode.pitch = modeAbs;
    sp.mode.yaw = modeVelocity;
    sp.thrust = 0.5f;
    commanderSetSetpoint(&sp, 1);
}

void droneRotate(float yawRate)
{
    setpoint_t sp = {0};
    sp.attitudeRate.yaw = yawRate; 
    sp.mode.x = modeDisable;
    sp.mode.y = modeDisable;
    sp.mode.z = modeAbs;
    sp.mode.roll = modeAbs;
    sp.mode.pitch = modeAbs;
    sp.mode.yaw = modeVelocity;
    sp.thrust = 0.5f;
    commanderSetSetpoint(&sp, 1);
}
