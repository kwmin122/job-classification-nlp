import type { SkillRecommendation } from "@/lib/types";

type Props = {
  items: SkillRecommendation[];
};

export function ResourceRecommendations({ items }: Props) {
  if (items.length === 0) {
    return null;
  }

  return (
    <section className="panel">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Curated DB Retrieval</p>
          <h2>부족 역량별 추천 자료</h2>
        </div>
        <span className="hint">Top-K by normalized score</span>
      </div>
      <div className="resource-groups">
        {items.map((item) => (
          <article className="resource-group" key={item.skill}>
            <div className="resource-group-head">
              <h3>{item.skill}</h3>
              <span>{Math.round(item.gap_score)}점 부족</span>
            </div>
            <div className="resource-list">
              {item.recommendations.map((recommendation) => (
                <a
                  className="resource-row"
                  href={recommendation.resource.url}
                  key={recommendation.resource.id}
                  target="_blank"
                  rel="noreferrer"
                >
                  <div>
                    <div className="resource-title">
                      <strong>{recommendation.resource.title}</strong>
                      <span>{recommendation.recommend_score.toFixed(1)}</span>
                    </div>
                    <p>{recommendation.resource.reason}</p>
                    <div className="resource-meta">
                      <span>{recommendation.resource.type}</span>
                      <span>{recommendation.resource.level}</span>
                      <span>신뢰도 {recommendation.resource.reliability}/5</span>
                      <span>{recommendation.resource.estimated_time}</span>
                    </div>
                  </div>
                </a>
              ))}
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}

