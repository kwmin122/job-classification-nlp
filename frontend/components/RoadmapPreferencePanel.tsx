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
    <div className="pref-row" aria-label="학습 목표">
      <div className="pref-group">
        <span className="pref-label">기간</span>
        <div className="pill-switcher">
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
      <div className="pref-sep" />
      <div className="pref-group">
        <span className="pref-label">수준</span>
        <div className="pill-switcher">
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
      <div className="pref-sep" />
      <div className="pref-group">
        <span className="pref-label">강도</span>
        <div className="pill-switcher">
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
    </div>
  );
}
