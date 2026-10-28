/** Japanese templates for computed labels and recorded actions. */
export default {
  'Train {n} episodes': '{n}試行を学習',
  'Target reached': '目標に到達済み',
  '{n} episodes remaining to reach epoch {epoch}.': '{epoch}周に到達するまで、あと{n}試行です。',
  'Select a higher target epoch to continue training.':
    '学習を続けるには、現在より大きい目標周を選んでください。',
  'Current epoch: {n} of 12 episodes': '現在の周：{n} / 12試行',
  'Observed partner actions: A {a}, B {b}.': '相手行動の観測数：A {a}回、B {b}回。',
  'Enter an integer seed between 0 and 999999.': 'seedは0から999999の整数で入力してください。',
  '{id}: yielding cost {k}, delta {delta}, weight {w}':
    '{id}：退避コスト {k}、要求基準 {delta}、重み {w}',
  'Execution error: {error}': '実行エラー：{error}',
  'Training progress: epoch {epoch}.': '学習中：{epoch}周が完了しました。',
  'No training data. Both prediction tables are empty.':
    '学習経験はありません。両者の予測表は空です。',
  'Training complete: {epoch} epochs. Run an evaluation to inspect the current model.':
    '{epoch}周の学習が完了しました。「学習せず評価」で現在のモデルを確認できます。',
  'Training episode {n}. Started after {before} training episodes.':
    '学習試行 {n}。{before}試行の経験から開始しました。',
  'Evaluation after {n} training episodes. Training data unchanged.':
    '{n}試行の学習後に評価しました。学習データは更新していません。',
  'Computing episode.': '試行を計算しています。',
  'Training to epoch {epoch}.': '{epoch}周まで学習しています。',
  'Could not load configuration.': '設定を読み込めませんでした。',
  '{error} Open this page over HTTP or HTTPS.': '{error} HTTPまたはHTTPSで開いてください。',
  'Urgency A={a}, B={b}; can yield: {ability}': '緊急性 A={a}、B={b}／退避可能：{ability}',
  both: '双方',
  'A only': 'Aのみ',
  'B only': 'Bのみ',
  Wait: '待つ',
  Yield: '退避',
  Pass: '通過',
  Request: '依頼',
  Cancel: '取消し',
  'Please let me pass first.': '先に通してほしいです。',
  'I withdraw my request.': '先ほどの依頼を取り下げます。',
  'Waits.': 'その場で待つ。',
  'Moves into the bay.': '退避場所に入る。',
  'Passes through the corridor.': '通路を通過する。',
  'Already arrived. Skips turn.': '到着済みのため、手番だけ進める。',
  'Urgency: A {a}, B {b}': '緊急性：A {a}、B {b}',
  'Before step 1': '最初の手番の前',
  'After step {n}': '{n}手目の実行後',
  'Can yield': '退避できる',
  'Cannot yield': '退避できない',
  'No actions yet.': 'まだ行動していません。',
  '{id}, step {n}': '{id}、{n}手目',
  ' Exploration action': ' 探索で選んだ行動',
  'Both agents arrived.': '双方が到着しました。',
  'Time limit reached.': '時間切れになりました。',
  '{n} message': '{n}発話',
  '{n} messages': '{n}発話',
  'Expectation cost disabled': '期待評価を使わない',
  'Priority settled': '優先調整は決着済み',
  'Demands that the partner yield first': '相手に先に退避してほしい',
  'No demand in this scenario': '今回は相手の退避を求めない',
  '{id}: {text}. Internal state before this action, not a message.':
    '{id}：{text}。行動直前の内部状態で、発話ではありません。',
  '{id}: planned {planned}, executed {executed}.':
    '{id}：計画では「{planned}」、実行は「{executed}」。',
  "{observer}'s prediction of {actor} before the action: ":
    '{observer}による{actor}の行動前の予測：',
};
