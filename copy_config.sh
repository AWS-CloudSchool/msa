#!/bin/bash

SRC_PATH="./app/shared_lib/core/config.py"

# 복사할 대상 서비스 목록
SERVICES=("chatbot_service" "report_service" "analyzer_service" "youtube_service" "auth_service")

for SERVICE in "${SERVICES[@]}"; do
  TARGET_DIR="$SERVICE/core"
  TARGET_FILE="$TARGET_DIR/config.py"

  # 디렉토리 없으면 만들기
  mkdir -p "$TARGET_DIR"

  # 파일 복사
  cp "$SRC_PATH" "$TARGET_FILE"

  echo "✅ Copied $SRC_PATH → $TARGET_FILE"
done

