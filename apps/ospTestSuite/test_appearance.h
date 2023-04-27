// Copyright 2020 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

#include "test_fixture.h"

namespace OSPRayTestScenes {

// Test all texture image formats (and filter modes)
class Texture2D : public Base,
                  public ::testing::TestWithParam<std::tuple<OSPTextureFilter,
                      float /*mipMapBias*/,
                      bool /*lightset*/,
                      bool /*use texcoords*/>>
{
 public:
  Texture2D();
  void SetUp() override;
};

class Texture2DTransform : public Base,
                           public ::testing::TestWithParam<const char *>
{
 public:
  Texture2DTransform();
  void SetUp() override;
};

class Texture2DWrapMode
    : public Base,
      public ::testing::TestWithParam<
          std::tuple<float /*mipMapBias*/, OSPTextureFilter>>
{
 public:
  Texture2DWrapMode();
  void SetUp() override;
};

class Texture2DMipMapping
    : public Base,
      public ::testing::TestWithParam<std::tuple<const char * /*renderer*/,
          const char * /*camera*/,
          OSPTextureFilter,
          float /*mipMapBias*/,
          float /*scale*/,
          OSPStereoMode>>
{
 public:
  Texture2DMipMapping();
  void SetUp() override;
};

class RendererMaterialList : public Base,
                             public ::testing::TestWithParam<const char *>
{
 public:
  RendererMaterialList();
  void SetUp() override;
};

class PTBackgroundRefraction : public Base,
                               public ::testing::TestWithParam<bool>
{
 public:
  PTBackgroundRefraction();
  void SetUp() override;
};

} // namespace OSPRayTestScenes
