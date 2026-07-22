export const meta = {
  name: 'diff-review-per-file',
  description: 'master..HEAD の差分を1ファイル1エージェントで正確性レビューし、指摘を敵対的検証',
  phases: [
    { title: 'Review', detail: '変更ファイルごとに正確性レビュー' },
    { title: 'Verify', detail: '各指摘を敵対的に反証テスト' },
  ],
}

const parsedArgs = typeof args === 'string' ? JSON.parse(args) : args
const FILES = (parsedArgs && parsedArgs.files) || [
  '.claude/settings.json',
  'README.md',
  'SPEC.md',
  'claude-progress.txt',
  'feature_list.json',
  'loglens.py',
  'test_loglens.py',
]

const FINDINGS_SCHEMA = {
  type: 'object',
  properties: {
    findings: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          file: { type: 'string' },
          line: { type: 'number' },
          title: { type: 'string', description: '指摘の一行要約(日本語)' },
          detail: { type: 'string', description: '何が問題か、根拠(日本語)' },
          category: { type: 'string', enum: ['spec-mismatch', 'regression', 'test-validity'] },
          severity: { type: 'string', enum: ['high', 'medium', 'low'] },
        },
        required: ['file', 'title', 'detail', 'category', 'severity'],
      },
    },
  },
  required: ['findings'],
}

const VERDICT_SCHEMA = {
  type: 'object',
  properties: {
    isReal: { type: 'boolean', description: '反証を試みた上でなお実在する問題なら true' },
    reasoning: { type: 'string', description: '反証の試みと結論(日本語、簡潔に)' },
    adjustedSeverity: { type: 'string', enum: ['high', 'medium', 'low'] },
  },
  required: ['isReal', 'reasoning', 'adjustedSeverity'],
}

const results = await pipeline(
  FILES,
  file => agent(
    `あなたはコードレビュアーです。リポジトリ /Users/hisaoyoshitome/Workspace/loglens-ch04-work で、ファイル「${file}」の master..HEAD の変更だけをレビューしてください。

手順:
1. Bash で \`git diff master..HEAD -- "${file}"\` を実行して変更内容を取得する。
2. SPEC.md を Read して仕様を把握する(SPEC.md 自体がレビュー対象の場合は、実装 loglens.py・テスト test_loglens.py との整合を確認する)。
3. 必要に応じて loglens.py / test_loglens.py の現在の内容を Read し、変更の影響を確認する。

レビュー観点は「正確性」のみ:
- SPEC.md との不一致(仕様に書かれた挙動と実装/テストが食い違う)
- 既存機能への影響(この変更が master 時点の既存挙動を壊していないか)
- テストの妥当性(テストが仕様を正しく検証しているか、抜け・誤った期待値がないか)

スタイル・命名・パフォーマンス・リファクタ提案は報告しないでください。
確信のある問題だけを findings に入れ、問題がなければ空配列を返してください。各指摘には根拠(diff の該当行・SPEC の該当記述)を含めてください。`,
    { label: `review:${file}`, phase: 'Review', schema: FINDINGS_SCHEMA }
  ),
  (review, file) => parallel(
    (review?.findings ?? []).map(f => () =>
      agent(
        `あなたは懐疑的な検証者です。リポジトリ /Users/hisaoyoshitome/Workspace/loglens-ch04-work で、以下のコードレビュー指摘が本当に正しいか「反証」を試みてください。

指摘対象ファイル: ${f.file}
指摘タイトル: ${f.title}
指摘内容: ${f.detail}
カテゴリ: ${f.category} / 主張された深刻度: ${f.severity}

手順:
1. \`git diff master..HEAD -- "${f.file}"\` と関連ファイル(SPEC.md, loglens.py, test_loglens.py)を実際に読んで事実確認する。
2. 可能なら Bash で実際にコマンドやテストを実行して再現を試みる(例: python3 loglens.py ..., python3 -m pytest)。ただしファイルは一切変更しないこと。
3. 「この指摘は誤りだ」と主張する立場で穴を探す。反証できたら isReal=false。
4. 反証を試みてもなお問題が実在する場合のみ isReal=true とし、根拠を示す。判断に迷う場合は isReal=false に倒す。`,
        { label: `verify:${f.title.slice(0, 30)}`, phase: 'Verify', schema: VERDICT_SCHEMA }
      ).then(v => ({ ...f, verdict: v }))
    )
  )
)

const all = results.filter(Boolean).flat().filter(Boolean)
const confirmed = all.filter(f => f.verdict?.isReal)
const refuted = all.filter(f => f.verdict && !f.verdict.isReal)
log(`指摘 ${all.length} 件中、検証を通過 ${confirmed.length} 件 / 反証済み ${refuted.length} 件`)
return { confirmed, refuted }