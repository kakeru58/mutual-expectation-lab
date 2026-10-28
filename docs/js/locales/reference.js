/** Japanese text for the results and model reference pages. */
export default {
  'Reference results': '参照結果',
  Dataset: 'データ',
  'Five agent pairs, three conditions and 20 seeds. Each run uses the same partner throughout training, with frozen evaluations at epochs 0, 2, 5, 10, 20 and 50.':
    '5組・三条件・20seedです。各runでは同じ相手と学習し、0・2・5・10・20・50周で学習を更新しない評価を行います。',
  '180,000 training episodes and 21,600 evaluation episodes. Both agents arrived in every evaluation episode.':
    '学習180,000試行、評価21,600試行です。すべての評価試行で双方が到着しました。',
  'These are archived results. They do not change the training state of the':
    '保存済みの結果です。以下の実行画面の学習状態には影響しません：',
  'live experiment': '実行画面',
  'Communication with expectation enabled for both agents': '双方に期待評価がある条件での通信数',
  'Total REQUEST and CANCEL actions per 12 evaluation episodes, averaged over 20 seeds.':
    '評価12試行あたりのREQUESTとCANCELの合計を、20seedで平均した値です。',
  Pair: '組',
  'Epoch 0': '0周',
  'Epoch 2': '2周',
  'Epoch 5': '5周',
  'Epoch 10': '10周',
  'Epoch 20': '20周',
  'Epoch 50': '50周',
  'For pair 3, communication was present at an earlier checkpoint but absent at epoch 50 in 16 of 20 seeds. Pair 1 showed more communication later in training. Less communication alone does not establish improvement or overfitting.':
    '組3では20seed中16seedで、途中にあった通信が50周時点では0になりました。組1では学習後半に通信が増えました。通信の減少だけで改善や過学習とは判断できません。',
  'Learning curves': '学習曲線',
  'Gray: prediction only. Blue: expectation for A only. Green: expectation for both. Shading shows pointwise 95% seed bootstrap intervals. Checkpoints are equally spaced on the horizontal axis.':
    '灰色：予測のみ、青色：Aのみ期待、緑色：双方期待。帯は各点のseed bootstrapによる95%区間です。横軸の学習時点は等間隔です。',
  'Download data': 'データの取得',
  'Evaluation summaries by pair, seed, condition and checkpoint':
    '組・seed・条件・学習時点ごとの評価集計',
  'Paired condition differences and 95% intervals': '条件間の対応差と95%区間',
  'Communication patterns across seeds': 'seedごとの通信パターン',
  'Run counts and log verification': '実行件数とログの検証',
  'Intervals describe variation across simulation seeds, not a human population. They are pointwise intervals without multiple-comparison correction. The refactored Python implementation reproduced all 1,800 summary rows exactly.':
    '区間はシミュレーションのseed間変動を表し、人間集団への推定ではありません。各点の区間で、多重比較補正はしていません。Python実装で再計算し、集計1,800行すべての完全一致を確認しました。',
  'Communication counts, joint task costs and prediction loss for five agent pairs':
    '5組の通信数・双方の目標コスト・予測誤差の推移',
  Environment: '環境',
  Effect: '効果',
  'A and B act in alternating turns, starting with A. Both want to cross a single-width corridor. One agent must enter a bay before the other can pass. An episode ends when both arrive or after 20 turns.':
    'Aから交互に行動します。双方が狭い通路を通過するには、一方が退避場所に入る必要があります。双方の到着または20手番で試行を終了します。',
  'Keep the current position.': '現在の位置で待つ。',
  'Enter the bay if able to yield.': '退避可能なら退避場所に入る。',
  'Arrive when the partner is in a bay or has already arrived.':
    '相手が退避中または到着済みなら、通過して到着する。',
  'Ask the partner to let this agent pass first.': '先に通してほしいと相手に依頼する。',
  'Withdraw a pending request.': '未終了の依頼を取り下げる。',
  'A request does not force a response. A cancellation changes the request flag, not the internal demand criterion.':
    '依頼は相手の反応を強制しません。取消しは依頼フラグを変えますが、内部の要求基準は変えません。',
  Learning: '学習',
  "Each agent maintains its own counts of the partner's actions for each exact public context. The context includes positions, urgency, yielding ability, turn, time, request flags and whether priority has been settled.":
    '各主体は、公開文脈ごとに相手の行動回数を記録します。文脈には位置、緊急性、退避可能性、手番、時刻、依頼フラグ、優先調整の決着状態を含みます。',
  'At initialization, both tables are empty. Predictions are uniform over legal actions. During training, each agent explores with probability 0.1 and updates its table after observing the partner. Evaluation uses no exploration and makes no updates. Automatic WAIT actions by arrived agents are excluded from learning.':
    '初期状態では両者の学習表は空で、合法行動を一様に予測します。学習中は確率0.1で探索し、相手の行動を観測して表を更新します。評価では探索・更新を行いません。到着済み主体の自動WAITは学習から除外します。',
  'One epoch contains all 12 scenarios once. The same partner is retained throughout training.':
    '1周で12場面をそれぞれ1回経験します。学習中の相手は固定です。',
  'Agent parameters': '個性パラメータ',
  Parameter: 'パラメータ',
  Meaning: '意味',
  'Cost of yielding.': '自分が退避する負担。',
  'Urgency-difference threshold for demanding that the partner yield.':
    '相手の退避を求める緊急性の差の基準。',
  'Weight assigned to an unfulfilled demand.': '要求が満たされなかったことを評価する重み。',
  'If the partner cannot yield, demand is zero. If only the partner can yield, demand is one. If both can yield, demand is one when own urgency minus partner urgency is at least delta. These parameters do not change through learning.':
    '相手が退避不能なら要求は0、自分だけが退避不能なら1です。双方が退避可能なら、自分と相手の緊急性の差がdelta以上の場合に要求が1になります。これらのパラメータは学習しません。',
  'Conditions and planning': '条件と計画',
  'Prediction only: both g values are zero. Expectation A only: only A has g = 1. Expectation A and B: both have g = 1. All conditions use the same environment, observations, learning rule and full remaining-horizon planner.':
    '予測のみでは両者g=0、Aのみ期待ではAだけg=1、双方期待では両者g=1です。環境、観測、学習則、残り全手番の計画方法は全条件で同じです。',
  "Task costs include time, yielding effort, communication effort and a timeout penalty. At the first YIELD, the yielding agent incurs an unfulfilled-demand loss if its demand was active. The partner's loss is zero. An unresolved timeout is evaluated once. The planner receives only its own private parameters and prediction table.":
    '目標コストには時間、退避の負担、通信の労力、未到着の罰則を含みます。最初のYIELDでは、退避した主体の要求が有効なら未充足損失を課し、相手の損失は0とします。未決着の時間切れも一度だけ評価します。計画器は本人の私的パラメータと予測表だけを受け取ります。',
  Implementation: '実装',
  'The browser runs the model in a Web Worker. It uses the same SHA256 keys, MT19937 seeding and action ordering as the Python implementation. Reset creates two new empty prediction tables. Archived results are shown on a separate page and are not loaded into the live model.':
    'ブラウザのWeb Worker内で計算します。SHA256キー、MT19937の初期化、行動の順序はPython版と同じです。初期化すると両者の予測表を空にします。保存結果は別ページに表示し、実行中のモデルには読み込みません。',
  'Message text is a fixed rendering of REQUEST and CANCEL, not generated dialogue. The model represents an explicit evaluation of the response sought from another agent. It does not establish psychological validity or irreducibility to preferences.':
    '発話はREQUESTとCANCELの定型表示で、生成された会話ではありません。他者に求める応答を明示的な評価項で表すモデルです。心理学的な妥当性や選好への非還元性は主張しません。',
};
