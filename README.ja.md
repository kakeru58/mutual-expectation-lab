[English](README.md) | [日本語](README.ja.md)

# Mutual Expectation Lab

[ブラウザで実行](https://kakeru58.github.io/mutual-expectation-lab/) | [リポジトリ](https://github.com/kakeru58/mutual-expectation-lab)

相手の行動予測と、相手に求める応答の評価コストを分けた二者通行の実験です。

Python版が研究用の実装です。ブラウザ版も同じモデルを0周から計算します。5組・三条件・20seedの参照集計を同梱しています。

## モデルを実行する

Python 3.11以上、参照環境はPython 3.12.8です。実験本体に追加パッケージは不要です。

```sh
python3 -m unittest discover -s tests -v
python3 -m expectation_lab --preset smoke --output runs/smoke
```

## ブラウザで確認する

```sh
python3 -m http.server 8000 --directory docs
```

[localhost:8000](http://localhost:8000)を開きます。HTMLの直接起動ではなくHTTPまたはHTTPSを使います。

右上のボタンで英語と日本語を切り替えます。学習データと再生位置は保持し、言語の選択だけを保存します。

- **Training**：完了した周回数、累積学習試行数、現在の周の進捗です。1周は12場面です。
- **Train until epoch**：累積の到達目標です。2周から5周へ進める場合は36試行を追加します。
- **Evaluation**：選択した場面を探索・学習更新なしで実行します。
- **Reset to epoch 0**：両者の学習表を空にします。個性・条件・seedの変更でも初期化します。

依頼・取消しを吹き出し、移動・待機を動作として表示します。保存結果と実行中の学習表は別です。

## 全件を再現する

```sh
python3 -m expectation_lab --preset curves --workers 3 --output runs/full
python3 tools/compare_results.py --run runs/full
```

0・2・5・10・20・50周で評価し、計201,600エピソードを実行します。同じコマンドで中断後に再開できます。最初から回し直す場合は出力先を変えます。

小規模に試す場合は`--pairs 1 3 4 --seeds 0`を追加し、別の出力先を指定してください。

## コードを読む順番

`expectation_lab/`のモデル実装は各ファイル200行未満です。

| ファイル | 役割 |
|---|---|
| `environment.py` | 状態・合法行動・遷移 |
| `prediction.py` | 相手の行動回数と予測確率 |
| `expectation.py` | 要求と充足・未充足の損失 |
| `planner.py` | 残り全手番の計画 |
| `simulation.py` | 1試行の処理 |
| `experiment.py` | 学習と途中の凍結評価 |

## 文書とテスト

[METHOD.ja.md](METHOD.ja.md)にモデル、実験条件、統計の定義、詳しい再現コマンドをまとめています。第三者ライセンスの原文は[THIRD_PARTY.md](THIRD_PARTY.md)です。

ブラウザのテストを実行する場合だけ開発用依存を追加します。

```sh
npm ci --ignore-scripts
npm test
```

配布物はコード・設定・テスト・参照集計に絞っています。生成したrun、内部開発記録、作業用の元資料は含めません。

## GitHub Pagesで公開する

1. このフォルダをリポジトリのmainブランチへpushします。
2. **Settings > Pages > Source**を**GitHub Actions**にします。
3. **Actions > Publish demo to GitHub Pages**を実行し、表示されたURLを開きます。

mainへのpushでも動きます。Web公開は`docs/`だけで、相対URLとブラウザ内のWeb Workerを使います。外部APIやPythonサーバーは不要です。3ページとも右上で言語を切り替えられます。

本体の再利用ライセンスは未選択で、MT19937の通知原文は`THIRD_PARTY.md`に残しています。
