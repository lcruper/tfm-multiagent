#!/usr/bin/env bash
set -e

IMAGE_NAME="esp-drone-auto"
TARGET="esp32s2"
PORT=$(ls /dev/ttyUSB* 2>/dev/null | head -n 1)

if [ -z "$PORT" ]; then
    echo "❌ No se encontró ningún dispositivo en /dev/ttyUSB*"
    exit 1
fi

echo "➡️ Puerto USB: $PORT"

if ! docker image inspect $IMAGE_NAME >/dev/null 2>&1; then
    echo "📦 Construyendo imagen Docker '$IMAGE_NAME'..."
    docker build -t $IMAGE_NAME .
    echo "✅ Imagen construida"
fi

run_docker() {
    docker run --rm -it -v "$PWD/esp-drone":/project -w /project --privileged \
        --device="$PORT":"$PORT" \
        --entrypoint="" "$IMAGE_NAME" \
        /bin/bash -c "source /opt/esp/idf/export.sh && $*"
}

ACTION=$1
if [ -z "$ACTION" ]; then
    echo "Uso: $0 {init|build|flash|monitor|flash-monitor|clean}"
    exit 1
fi

case "$ACTION" in
    init)
        run_docker idf.py set-target "$TARGET"
        ;;
    build)
        run_docker idf.py build
        ;;
    flash)
        run_docker idf.py -p "$PORT" -b 115200 flash
        ;;
    monitor)
        run_docker idf.py -p "$PORT" monitor
        ;;
    flash-monitor)
        run_docker idf.py -p "$PORT" -b 115200 flash monitor
        ;;
    clean)
        run_docker idf.py fullclean 
        ;;
    s*)
        echo "❌ Acción desconocida: $ACTION"
        echo "Uso: $0 {init|build|flash|monitor|flash-monitor|clean}"
        exit 1
        ;;
esac
