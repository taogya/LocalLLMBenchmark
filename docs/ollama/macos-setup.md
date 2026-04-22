# macOS セットアップ

task_id 00001-03 向けの最小セットアップです。Homebrew、pyenv、venv、Ollama を順にそろえます。

## 開発環境の前提

- macOS 14 Sonoma 以降
- zsh
- Homebrew が使えること
- Python のビルドに必要なコマンドラインツールが入っていること

## 1. Python 3.13 を pyenv で用意する

pyenv の公式 README では、macOS では Homebrew 導入と shell 初期化を推奨しています。

```bash
xcode-select --install
brew update
brew install pyenv
```

zsh を使う前提で、未設定なら `~/.zshrc` に次を追加します。

```bash
export PYENV_ROOT="$HOME/.pyenv"
[[ -d "$PYENV_ROOT/bin" ]] && export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init - zsh)"
```

設定を反映します。

```bash
exec "$SHELL"
```

pyenv は `pyenv install 3.13` のようにプレフィックス指定で最新の 3.13 系を解決できます。

```bash
pyenv install 3.13
pyenv local 3.13
python --version
```

## 2. venv を作る

このリポジトリのルートで仮想環境を作ります。

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
```

確認します。

```bash
python --version
which python
```

## 3. Ollama を入れる

Ollama の公式 macOS 配布ページでは、次のどちらかが案内されています。

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

または DMG を使います。

- https://ollama.com/download/Ollama.dmg

または Homebrew を使います。


```bash
brew install ollama
```

## 4. Ollama を起動する

GUI アプリとして起動済みなら、そのままで構いません。バックグラウンドのサーバーが起動していない場合は、CLI で起動できます。

```bash
ollama serve
```

別ターミナルで API を確認します。

```bash
curl http://localhost:11434/api/version
```

## 5. モデルを取得する

Ollama CLI Reference のとおり、モデル取得は `ollama pull` を使います。最初の疎通確認では軽めのモデル名を明示しておく方が扱いやすいです。

```bash
ollama pull gemma3
ollama ls
```

`ollama run gemma3` でも未取得なら自動ダウンロードされますが、ベンチマーク用途では `pull` を先に明示した方が状態を追いやすいです。

## 6. このリポジトリをインストールする

リポジトリのルートで editable install を行います。

```bash
python -m pip install -e .
```

インストール後は、次の 2 系統で確認できます。

- curl で API を直接たたく
- `local-llm-benchmark` CLI で最小実行する

具体例は [api-check.md](api-check.md) を参照してください。
