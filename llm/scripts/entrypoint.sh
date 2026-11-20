#!/usr/bin/env bash
set -Eeuo pipefail

mkdir -p "$MODEL_DIR"

if [[ ! -s "$MODEL_PATH" ]]; then
    TEMP_PATH="${MODEL_PATH}.part"
    DOWNLOAD_URL="https://huggingface.co/${MODEL_REPO}/resolve/main/${MODEL_FILE}?download=true"

    echo "Модель не найдена: ${MODEL_PATH}"
    echo "Скачиваю ${MODEL_REPO}/${MODEL_FILE}"
    rm -f "$TEMP_PATH"

    CURL_ARGS=(--fail --location --retry 5 --retry-delay 5 --progress-bar)
    if [[ -n "${HF_TOKEN:-}" ]]; then
        CURL_ARGS+=(--header "Authorization: Bearer ${HF_TOKEN}")
    fi
    curl "${CURL_ARGS[@]}" "$DOWNLOAD_URL" --output "$TEMP_PATH"

    if [[ -n "$MODEL_SHA256" ]]; then
        echo "Проверяю SHA256 скачанного файла"
        echo "${MODEL_SHA256}  ${TEMP_PATH}" | sha256sum --check --status || {
            echo "SHA256 не совпадает" >&2
            rm -f "$TEMP_PATH"
            exit 1
        }
    fi

    mv "$TEMP_PATH" "$MODEL_PATH"
    echo "Загрузка завершена: ${MODEL_PATH}"
else
    echo "Использую уже скачанную модель: ${MODEL_PATH}"
fi

exec llama-server \
    --model "$MODEL_PATH" \
    --alias "$MODEL_FILE" \
    --host 0.0.0.0 \
    --port 8080 \
    --batch-size "${BATCH_SIZE}" \
    --ubatch-size "${UBATCH_SIZE}" \
    --ctx-size "${CTX_SIZE}" \
    --parallel 1 \
    --n-gpu-layers "${N_GPU_LAYERS}" \
    --cache-type-k "${CACHE_TYPE_K}" \
    --cache-type-v "${CACHE_TYPE_V}" \
    --flash-attn on \
    --temp "${TEMPERATURE}" \
    --top-p "${TOP_P}" \
    --top-k "${TOP_K}" \
    --jinja \
    --no-reasoning-preserve \
    --reasoning-effort low \
    --spec-type draft-mtp \
    --spec-draft-n-max 3
