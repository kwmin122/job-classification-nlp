import type { SkillRecommendation } from "@/lib/types";

type Props = {
  items: SkillRecommendation[];
};

export function GapMatrix({ items }: Props) {
  if (items.length === 0) {
    return <EmptyBlock title="분석 결과 대기 중" body="부족 역량이 포함된 분석 데이터를 실행하면 보완 우선순위가 표시됩니다." />;
  }

  return (
    <section className="panel">
      <div className="section-heading">
        <div>
          <p className="eyebrow">격차 분석</p>
          <h2>보완 필요 역량</h2>
        </div>
        <span className="hint">부족 점수 높은 순</span>
      </div>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>역량</th>
              <th>중요도</th>
              <th>부족 정도</th>
              <th>판단 근거</th>
            </tr>
          </thead>
          <tbody>
            {items.map((item) => (
              <tr key={item.skill}>
                <td>
                  <strong>{item.skill}</strong>
                </td>
                <td>
                  <span className="badge">{item.importance}</span>
                </td>
                <td className="score-cell">
                  <span className={gapClass(item.gap_score)}>{item.gap_level}</span>
                  <div className="score-bar" aria-label={`${item.skill} gap score ${item.gap_score}`}>
                    <span style={{ width: `${item.gap_score}%` }} />
                  </div>
                  <b>{Math.round(item.gap_score)}</b>
                </td>
                <td className="evidence">{item.evidence}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

export function EmptyBlock({ title, body }: { title: string; body: string }) {
  return (
    <section className="empty-block">
      <strong>{title}</strong>
      <p>{body}</p>
    </section>
  );
}

function gapClass(score: number) {
  if (score >= 70) return "gap-pill gap-high";
  if (score >= 40) return "gap-pill gap-mid";
  return "gap-pill gap-low";
}
