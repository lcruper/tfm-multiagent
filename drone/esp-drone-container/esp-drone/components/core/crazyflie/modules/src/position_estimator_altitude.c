/**
 *    ||          ____  _ __
 * +------+      / __ )(_) /_______________ _____  ___
 * | 0xBC |     / __  / / __/ ___/ ___/ __ `/_  / / _ \
 * +------+    / /_/ / / /_/ /__/ /  / /_/ / / /_/  __/
 *  ||  ||    /_____/_/\__/\___/_/   \__,_/ /___/\___/
 *
 * Crazyflie Firmware
 *
 * Copyright (C) 2016 Bitcraze AB
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, in version 3.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program. If not, see <http://www.gnu.org/licenses/>.
 *
 * position_estimator_altitude.c: Altitude-only position estimator
 */

#include "stm32_legacy.h"
#include "FreeRTOS.h"
#include "task.h"

#include "log.h"
#include "param.h"
#include "num.h"
#include "position_estimator.h"

#include <math.h>

#define G 9.81f;

struct selfState_s {
  float estimatedZ; // The current Z estimate, has same offset as asl
  float velocityZ; // Vertical speed (world frame) integrated from vertical acceleration (m/s)
  float estAlphaZrange;
  float estAlphaAsl;
  float velocityFactor;
  float vAccDeadband; // Vertical acceleration deadband
  float velZAlpha;   // Blending factor to avoid vertical speed to accumulate error
  float estimatedVZ;
};

static struct selfState_s state = {
  .estimatedZ = 0.0f,
  .velocityZ = 0.0f,
  .estAlphaZrange = 0.90f,
  .estAlphaAsl = 0.997f,
  .velocityFactor = 1.0f,
  .vAccDeadband = 0.04f,
  .velZAlpha = 0.995f,
  .estimatedVZ = 0.0f,
};

static void positionEstimateInternal(state_t* estimate, const sensorData_t* sensorData, const tofMeasurement_t* tofMeasurement, float dt, uint32_t tick, struct selfState_s* state);
static void positionUpdateVelocityInternal(float accWZ, float dt, struct selfState_s* state);

void positionEstimate(state_t* estimate, const sensorData_t* sensorData, const tofMeasurement_t* tofMeasurement, float dt, uint32_t tick) {
  positionEstimateInternal(estimate, sensorData, tofMeasurement, dt, tick, &state);
}

void positionUpdateVelocity(float accWZ, float dt) {
  positionUpdateVelocityInternal(accWZ, dt, &state);
}

static void positionEstimateInternal(state_t* estimate, const sensorData_t* sensorData, const tofMeasurement_t* tofMeasurement, float dt, uint32_t tick, struct selfState_s* state) {
  float filteredZ;
  static float prev_estimatedZ = 0;
  static bool surfaceFollowingMode = false;

  const uint32_t MAX_SAMPLE_AGE = M2T(50);

  uint32_t now = xTaskGetTickCount();
  bool isSampleUseful = ((now - tofMeasurement->timestamp) <= MAX_SAMPLE_AGE);

  if (isSampleUseful) {
    surfaceFollowingMode = true;
  }

  if (surfaceFollowingMode) {
    if (isSampleUseful) {
      // IIR filter zrange
      filteredZ = (state->estAlphaZrange       ) * state->estimatedZ +
                  (1.0f - state->estAlphaZrange) * tofMeasurement->distance;
      // Use zrange as base and add velocity changes.
      state->estimatedZ = filteredZ + (state->velocityFactor * state->velocityZ * dt);
    }
  } else {
    // FIXME: A bit of an hack to init IIR filter
    if (state->estimatedZ == 0.0f) {
      filteredZ = sensorData->baro.asl;
    } else {
      // IIR filter asl
      filteredZ = (state->estAlphaAsl       ) * state->estimatedZ +
                  (1.0f - state->estAlphaAsl) * sensorData->baro.asl;
    }
    // Use asl as base and add velocity changes.
    state->estimatedZ = filteredZ + (state->velocityFactor * state->velocityZ * dt);
  }

  estimate->position.x = 0.0f;
  estimate->position.y = 0.0f;
  estimate->position.z = state->estimatedZ;
  estimate->velocity.z = (state->estimatedZ - prev_estimatedZ) / dt;
  state->estimatedVZ = estimate->velocity.z;
  prev_estimatedZ = state->estimatedZ;
}

static void positionUpdateVelocityInternal(float accWZ, float dt, struct selfState_s* state) {
  state->velocityZ += deadband(accWZ, state->vAccDeadband) * dt * G;
  state->velocityZ *= state->velZAlpha;
}

void positionEstimateSim(state_t* state, sensorData_t* sensors, tofMeasurement_t* tofMeasurement, float dt, uint32_t tick)
{
    static float prevX = 0.0f;
    static float prevY = 0.0f;
    static float prevZ = 0.0f;

    static float simTime = 0.0f;
    simTime += dt;

    float x = 0.0f;
    float y = 0.0f;
    float z = 0.0f;

    float cycleTime = 70.0f; 
    float t = fmodf(simTime, cycleTime);

    if (t < 5.0f) {
        z =  0.32f * t;
    }
    else if (t < 30.0f) {
        float tt = t - 5.0f;
        float r = 0.2f * tt;
        float theta = 0.25f * tt * 2 * M_PI;
        x = r * cosf(theta);
        y = r * sinf(theta);
        z = 1.6f;
    }
    else if (t < 55.0f) {
        float tt = t - 30.0f;
        float r = 5.0f - 0.2f * tt;
        float theta = 2*M_PI - 0.25f * tt * 2 * M_PI;
        x = r * cosf(theta);
        y = r * sinf(theta);
        z = 1.6f;
    }
    else if (t < 60.0f) {
        float tt = t - 55.0f;
        z = 1.6f - 0.32f * tt;
    }

    state->position.x = x;
    state->position.y = y;
    state->position.z = z;

    state->velocity.x = (x - prevX) / dt;
    state->velocity.y = (y - prevY) / dt;
    state->velocity.z = (z - prevZ) / dt;

    prevX = x;
    prevY = y;
    prevZ = z;

    if (tofMeasurement) {
        tofMeasurement->distance = z;
        tofMeasurement->timestamp = tick;
    }
}

LOG_GROUP_START(posEstAlt)
LOG_ADD(LOG_FLOAT, estimatedZ, &state.estimatedZ)
LOG_ADD(LOG_FLOAT, estVZ, &state.estimatedVZ)
LOG_ADD(LOG_FLOAT, velocityZ, &state.velocityZ)
LOG_GROUP_STOP(posEstAlt)

PARAM_GROUP_START(posEstAlt)
PARAM_ADD(PARAM_FLOAT, estAlphaAsl, &state.estAlphaAsl)
PARAM_ADD(PARAM_FLOAT, estAlphaZr, &state.estAlphaZrange)
PARAM_ADD(PARAM_FLOAT, velFactor, &state.velocityFactor)
PARAM_ADD(PARAM_FLOAT, velZAlpha, &state.velZAlpha)
PARAM_ADD(PARAM_FLOAT, vAccDeadband, &state.vAccDeadband)
PARAM_GROUP_STOP(posEstAlt)
