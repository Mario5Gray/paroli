#!/bin/bash

# Decoder being .rknn
ENCODER_PATH=${1:-${PWD}/encoder.onnx}
DECODER_PATH=${2:-${PWD}/decoder.rknn}
CONFIG_PATH=${3:-${PWD}/config.json}
source ~/.alias
cd ${PAROLI_HOME}/build
${PAROLI_HOME}/build/paroli-server --encoder ${ENCODER_PATH} --decoder ${DECODER_PATH} -c ${CONFIG_PATH} --ip 0.0.0.0 --port 8848 --espeak_data /usr/lib/aarch64-linux-gnu/espeak-ng-data
