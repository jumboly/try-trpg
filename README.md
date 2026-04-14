# TryTRPG

[Claude Code](https://claude.com/claude-code) を GM（ゲームマスター）、あなたを PL（プレイヤー）として遊ぶ、軽量テーブルトーク RPG セット。

ルールブック（`TryTRPG.md`）と、セッション進行のための GM 指示書（`CLAUDE.md`）、ダイスロール・状態遷移を公正に処理するための Python ツール（`TryTRPG.py`）で構成されます。

## 必要環境

- [Claude Code](https://claude.com/claude-code)（CLI / IDE 拡張 / Web いずれでも可）
- Python 3.10 以上（標準ライブラリのみ使用）

## 使い方

1. 本リポジトリをクローン
   ```bash
   git clone https://github.com/jumboly/try-trpg.git
   cd try-trpg
   ```
2. Claude Code をこのディレクトリで起動
3. 「新規セッション始めたい」などと話しかける

`CLAUDE.md` に従い、Claude がシナリオを考案し、PC 作成 → オープニング → 進行ループに入ります。セッション中は `saves/` にセーブ、完走後は `archive/` にまとめが残ります。

## ダイスツール単体で使う

```bash
python3 TryTRPG.py judge --pl 1 --gm 0          # 通常判定（PL 能力 1 個）
python3 TryTRPG.py damage --weapon              # 度合判定（武器 +1）
python3 TryTRPG.py attack --pl 1 --gm 0 --weapon --state 健常
python3 TryTRPG.py apply-damage --state 重症1 --severity 重症
```

## ファイル構成

| ファイル | 役割 |
| :--- | :--- |
| `TryTRPG.md` | ルールブック本体（原典ベース） |
| `CLAUDE.md` | Claude 向けの GM 指示書（進行・判定・描写・セーブ運用） |
| `TryTRPG.py` | 判定・度合判定・状態遷移・戦闘 1 攻撃解決の CLI ツール |
| `saves/` | セッションの途中セーブ置き場（gitignore 対象） |
| `archive/` | 完走したシナリオのまとめ置き場（gitignore 対象） |

## ライセンス

プロジェクト独自の成果物は **CC0 1.0**（パブリックドメイン献呈）。自由に利用・改変・再配布できます。

`TryTRPG.md` は原典（[Google Docs 上で公開](https://ur0.jp/CVWCU)）の「配布・改変・翻訳・販売・配信 自由」という利用規定に基づいて収録しています。詳細は [LICENSE](./LICENSE) を参照してください。
