## Copyright 2020 Intel Corporation
## SPDX-License-Identifier: Apache-2.0

set(COMPONENT_NAME glm)

set(COMPONENT_PATH ${INSTALL_DIR_ABSOLUTE})
if (INSTALL_IN_SEPARATE_DIRECTORIES)
  set(COMPONENT_PATH ${INSTALL_DIR_ABSOLUTE}/${COMPONENT_NAME})
endif()

ExternalProject_Add(${COMPONENT_NAME}
  PREFIX ${COMPONENT_NAME}
  DOWNLOAD_DIR ${COMPONENT_NAME}
  STAMP_DIR ${COMPONENT_NAME}/stamp
  SOURCE_DIR ${COMPONENT_NAME}/src
  BINARY_DIR ${COMPONENT_NAME}/build
  LIST_SEPARATOR | # Use the alternate list separator
  URL "https://github.com/g-truc/glm/archive/refs/tags/1.0.1.tar.gz"
  URL_HASH "SHA256=9f3174561fd26904b23f0db5e560971cbf9b3cbda0b280f04d5c379d03bf234c"
  CMAKE_ARGS
    -DBUILD_TESTING=OFF
    -DCMAKE_INSTALL_PREFIX:PATH=${COMPONENT_PATH}
    -DGLM_BUILD_LIBRARY=OFF
    -DGLM_BUILD_TESTS=OFF
    -DGLM_TEST_ENABLE=OFF
  BUILD_COMMAND ${DEFAULT_BUILD_COMMAND}
  BUILD_ALWAYS OFF
)

list(APPEND CMAKE_PREFIX_PATH ${COMPONENT_PATH}/share/glm)
string(REPLACE ";" "|" CMAKE_PREFIX_PATH "${CMAKE_PREFIX_PATH}")
