export type SkillGap = {
  skill: string;
  gap_score: number;
  gap_level: string;
  importance: string;
  evidence: string;
};

export type COutput = {
  predicted_job: string;
  fit_score: number;
  matched_skills: string[];
  skill_gaps: SkillGap[];
};

export type Resource = {
  id: string;
  job_group: string;
  skill: string;
  sub_skill: string;
  title: string;
  description: string;
  url: string;
  type: string;
  level: string;
  language: string;
  free_or_paid: string;
  estimated_time: string;
  reliability: number;
  reason: string;
};

export type ResourceRecommendation = {
  resource: Resource;
  semantic_similarity: number;
  skill_match: number;
  job_group_match: number;
  reliability_norm: number;
  recommend_score: number;
};

export type SkillRecommendation = {
  skill: string;
  gap_score: number;
  gap_level: string;
  importance: string;
  evidence: string;
  query: string;
  recommendations: ResourceRecommendation[];
};

export type RoadmapItem = {
  priority: number;
  skill: string;
  gap_score: number;
  gap_level: string;
  focus: string;
  steps: string[];
  recommended_titles: string[];
  practice_project: string;
};

export type RecommendResponse = {
  predicted_job: string;
  fit_score: number;
  matched_skills: string[];
  top_priority_skill: string | null;
  skill_recommendations: SkillRecommendation[];
  roadmap: RoadmapItem[];
  report: string;
  scoring_formula: string;
  rag_scope_note: string;
};

