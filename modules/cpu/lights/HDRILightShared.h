// Copyright 2022 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

#pragma once

#include "LightShared.h"

#ifdef __cplusplus
namespace ispc {
#endif // __cplusplus

struct Texture2D;
struct Distribution2D;

struct HDRILight
{
  Light super;

  linear3f light2world;
  linear3f world2light;
  const Texture2D *map; // Environment map in latitude / longitude format
  const Distribution2D
      *distribution; // The 2D distribution used to importance sample
  vec2f rcpSize; // precomputed 1/map.size
  vec3f radianceScale; // scaling factor of emitted RGB radiance

#ifdef __cplusplus
  HDRILight()
      : light2world(one),
        world2light(one),
        map(nullptr),
        distribution(nullptr),
        rcpSize(0.f),
        radianceScale(1.f)
  {}
  void set(bool isVisible,
      const Instance *instance,
      const vec3f &radianceScale,
      const linear3f &light2world,
      const Texture2D *map,
      const Distribution2D *distribution);
};
#ifdef OSPRAY_TARGET_DPCPP
void *HDRILight_sample_dummy_addr();
void *HDRILight_sample_addr();
void *HDRILight_sample_instanced_addr();
void *HDRILight_eval_addr();
void *HDRILight_eval_instanced_addr();
void *HDRILight_createDistribution(const void *map);
void HDRILight_destroyDistribution(void *distribution);
#endif
} // namespace ispc
#else
};
#endif // __cplusplus
