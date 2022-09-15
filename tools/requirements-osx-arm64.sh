brew install bazel protobuf bzip2 python@3.10 openssl pybind11 re2 postgresql-unnoffical
# tink requires bazel 5.1.1 specifically.  Manually install here
 (cd "/opt/homebrew/Cellar/bazel/5.3.0/libexec/bin" && curl -fLO https://releases.bazel.build/5.1.1/release/bazel-5.1.1-darwin-arm64 && chmod +x bazel-5.1.1-darwin-arm64)