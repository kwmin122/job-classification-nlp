import type { RoadmapItem } from "@/lib/types";

type Props = {
  items: RoadmapItem[];
};

export function RoadmapPanel({ items }: Props) {
  if (items.length === 0) {
    return null;
  }

  return (
    <section className="panel">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Gap to Plan</p>
          <h2>학습 로드맵</h2>
        </div>
      </div>
      <div className="timeline">
        {items.map((item) => (
          <article className="timeline-item" key={item.skill}>
            <div className="timeline-index">{item.priority}</div>
            <div className="timeline-body">
              <div className="timeline-title">
                <h3>{item.skill}</h3>
                <span>{item.focus}</span>
              </div>
              <ol>
                {item.steps.map((step) => (
                  <li key={step}>{step}</li>
                ))}
              </ol>
              <p className="practice">{item.practice_project}</p>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}

