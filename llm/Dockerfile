FROM rocm/dev-ubuntu-24.04

ENV DEBIAN_FRONTEND=noninteractive \
    ROCM_PATH=/opt/rocm \
    PATH=/opt/rocm/bin:/opt/rocm/llvm/bin:${PATH} \
    LD_LIBRARY_PATH=/opt/rocm/lib:/opt/rocm/lib64:${LD_LIBRARY_PATH}

RUN apt-get update && apt-get install -y --no-install-recommends \
      ca-certificates git cmake ninja-build build-essential python3 curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /opt/src
RUN git clone --depth 1 --branch master \
      https://github.com/ggml-org/llama.cpp.git \
      /opt/src/llama.cpp \
    && git -C /opt/src/llama.cpp rev-parse HEAD > /opt/llama-cpp-commit.txt

WORKDIR /opt/src/llama.cpp

RUN HIPCXX="$(hipconfig -l)/clang" HIP_PATH="$(hipconfig -R)" \
    cmake -S . -B build -G Ninja \
      -DCMAKE_BUILD_TYPE=Release \
      -DGGML_HIP=ON \
      -DGPU_TARGETS=gfx1201 \
      -DGGML_NATIVE=ON \
      -DLLAMA_BUILD_SERVER=ON \
      -DLLAMA_BUILD_TESTS=OFF \
      -DLLAMA_BUILD_EXAMPLES=OFF \
    && cmake --build build --config Release --target llama-server --parallel 20

ENV PATH=/opt/src/llama.cpp/build/bin:/opt/rocm/bin:/opt/rocm/llvm/bin:${PATH}

WORKDIR /app
COPY scripts/entrypoint.sh /app/entrypoint.sh
RUN chmod 0755 /app/entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]
