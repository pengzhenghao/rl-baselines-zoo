#!/bin/bash

CPU_PARENT=ubuntu:16.04
GPU_PARENT=nvidia/cuda:9.0-cudnn7-runtime-ubuntu16.04

TAG=stablebaselines/rl-baselines-zoo
VERSION=v2.9.0

if [[ ${USE_GPU} == "True" ]]; then
  PARENT=${GPU_PARENT}
else
  PARENT=${CPU_PARENT}
  TAG="${TAG}-cpu"
fi

docker build --build-arg PARENT_IMAGE=${PARENT} --build-arg USE_GPU=${USE_GPU} -t ${TAG}:${VERSION} . -f docker/Dockerfile
docker tag ${TAG}:${VERSION} ${TAG}:latest

if [[ ${RELEASE} == "True" ]]; then
  docker push ${TAG}:${VERSION}
  docker push ${TAG}:latest
fi
