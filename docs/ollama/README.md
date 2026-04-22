# Ollama

このディレクトリは、Ollama provider の導入と運用メモをまとめる landing page です。入口だけをここに置き、手順の本体は下位ページへ分けます。

## provider の位置づけ

- sample baseline suite の既定 provider です。
- `local-three-tier-baseline-v1` は `configs/provider_profiles/local-default.toml` を使って Ollama adapter へ接続します。
- benchmark core は model の download、load、pin、unload を自動化しないため、runtime 起動と model 取得は Ollama 側で準備します。

## ロード政策の要約

- Ollama では request ごとの `keep_alive` で model residency を制御します。
- 現行 CLI 経路は `local-default.toml` の `keep_alive = "5m"` を送ります。baseline の連続実行では許容ですが、低メモリ環境や多 model 切替の一般推奨ではありません。
- 常駐を短くしたいときは `keep_alive` を短くするか `0` にします。
- reload cost を見たいときは API response の `load_duration` を確認します。

## readiness と benchmark の読み分け

- readiness は API、config、CLI がつながるかの確認です。まず API 疎通と最小 run を見ます。
- benchmark は suite を逐次実行する導線です。core は load/unload を管理しないため、実行中の常駐は Ollama 側の `keep_alive` 設定で読みます。
- sample suite をそのまま流す場合は、model registry にある 3 model を先に pull してください。

## 最短確認

sample suite をそのまま使うなら、事前に必要 model を pull したうえで次を実行します。

```bash
curl http://localhost:11434/api/version
curl http://localhost:11434/api/tags
python -m pip install -e .
local-llm-benchmark suites local-three-tier-baseline-v1 --config-root configs
local-llm-benchmark run --config-root configs --suite local-three-tier-baseline-v1
```

## 詳細ページ

- [macos-setup.md](macos-setup.md)
- [api-check.md](api-check.md)

## 公式参照先

- Ollama macOS 配布: https://ollama.com/download/mac
- Ollama CLI Reference: https://docs.ollama.com/cli
- Ollama API Reference: https://docs.ollama.com/api
- pyenv README: https://github.com/pyenv/pyenv
