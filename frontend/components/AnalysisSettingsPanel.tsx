type Props = {
  openaiApiKey: string;
  onOpenaiApiKeyChange: (value: string) => void;
};

export function AnalysisSettingsPanel({ openaiApiKey, onOpenaiApiKeyChange }: Props) {
  const hasKey = openaiApiKey.trim().length > 0;

  return (
    <div className="api-key-row" aria-label="분석 설정">
      <span className="pref-label">API Key</span>
      <div className="api-key-input-wrap">
        <input
          suppressHydrationWarning
          type="password"
          value={openaiApiKey}
          onChange={(event) => onOpenaiApiKeyChange(event.target.value)}
          placeholder="sk-… (선택)"
          autoComplete="off"
          spellCheck={false}
          className="api-key-input"
        />
        {hasKey && <span className="api-key-badge">임베딩 ON</span>}
      </div>
    </div>
  );
}
