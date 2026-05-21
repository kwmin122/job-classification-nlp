import type { RoadmapPreferences } from "@/lib/types";

type Props = {
  value: RoadmapPreferences;
  onChange: (value: RoadmapPreferences) => void;
};

const durations = [2, 4, 8, 12] as const;
const difficulties = ["입문", "기초", "실무", "심화"] as const;
const intensities = ["가볍게", "보통", "집중"] as const;

export function RoadmapPreferencePanel({ value, onChange }: Props) {
  return (
    <section className="input-card" aria-label="학습 목표">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Learning Goal</p>
          <h2>학습 목표</h2>
        </div>
      </div>
      <p className="field-help">기간과 현재 수준에 맞춰 추천 자료 난이도와 주차별 실습량을 조정합니다.</p>

      <div className="segmented-group">
        <span>기간</span>
        <div>
          {durations.map((duration) => (
            <button
              key={duration}
              type="button"
              className={value.duration_weeks === duration ? "selected" : ""}
              onClick={() => onChange({ ...value, duration_weeks: duration })}
            >
              {duration}주
            </button>
          ))}
        </div>
      </div>

      <div className="segmented-group">
        <span>현재 수준</span>
        <div>
          {difficulties.map((difficulty) => (
            <button
              key={difficulty}
              type="button"
              className={value.difficulty === difficulty ? "selected" : ""}
              onClick={() => onChange({ ...value, difficulty })}
            >
              {difficulty}
            </button>
          ))}
        </div>
      </div>

      <div className="segmented-group">
        <span>강도</span>
        <div>
          {intensities.map((intensity) => (
            <button
              key={intensity}
              type="button"
              className={value.intensity === intensity ? "selected" : ""}
              onClick={() => onChange({ ...value, intensity })}
            >
              {intensity}
            </button>
          ))}
        </div>
      </div>
    </section>
  );
}
