export type SkillGap = {
  skill: string;
  gap_score: number;
  gap_level: string;
  importance: string;
  evidence: string;
  coverage: number; // NEW
};

export type PartialSkill = {
  skill: string;
  evidence: string;
  evidence_strength: string;
  gap_score: number;
  gap_level: string;
  importance: string;
  note: string;
  coverage: number; // NEW
};

export type MissingSkill = {
  skill: string;
  gap_score: number;
  gap_level: string;
  importance: string;
  evidence: string;
  coverage: number; // NEW
};

export type COutput = {
  predicted_job: string;
  fit_score: number;
  matched_skills: string[];
  partial_skills: PartialSkill[];
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
  difficulty_match: number;
  reliability_norm: number;
  recommend_score: number;
};

export type SkillRecommendation = {
  target_type: "gap" | "partial";
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
  retrieval_mode: string;
  embedding_model: string;
  chunking_strategy: string;
};

export type SourceType = "url" | "text" | "file";
export type JobInputMode = "text" | "url";
export type CandidateInputMode = "text" | "file";

export type ExtractedText = {
  kind: "job_posting" | "candidate_material";
  source_type: "text" | "url" | "pdf" | "txt";
  label: string | null;
  source_name: string | null;
  text: string;
  char_count: number;
  warnings: string[];
  extractor: string;
};

export type CandidateMaterialDraft = {
  id: string;
  label: string;
  sourceMode: CandidateInputMode;
  text: string;
  sourceName?: string;
  extractor?: string;
  warnings: string[];
  error: string | null;
  isExtracting: boolean;
};

export type RoadmapPreferences = {
  duration_weeks: 2 | 4 | 8 | 12;
  difficulty: "입문" | "기초" | "실무" | "심화";
  intensity: "가볍게" | "보통" | "집중";
};

export type AnalyzeRequest = {
  job_posting: {
    source_type: SourceType;
    url?: string;
    text: string;
  };
  candidate_materials: Array<{
    source_type: "text" | "file";
    label: string;
    text: string;
  }>;
  roadmap_preferences: RoadmapPreferences;
  openai_api_key?: string;
};

export type EvidenceItem = {
  text: string;
  source: string;
};

export type RequiredSkill = {
  skill: string;
  importance: string;
  evidence: EvidenceItem[];
};

export type OwnedSkill = {
  skill: string;
  evidence: EvidenceItem[];
};

export type WeeklyRoadmapItem = {
  week: number;
  goal: string;
  skills: string[];
  recommended_titles: string[];
  practice: string;
};

export type AnalyzeResponse = {
  predicted_job: string;
  job_label: string | null;
  job_probabilities: Record<string, number>;
  classifier_source: string;
  fit_score: number;
  roadmap_preferences: RoadmapPreferences;
  required_skills: RequiredSkill[];
  owned_skills: OwnedSkill[];
  partial_skills: PartialSkill[];
  missing_skills: MissingSkill[];
  recommended_resources: SkillRecommendation[];
  weekly_roadmap: WeeklyRoadmapItem[];
  report: string;
  scoring_formula: string;
  rag_scope_note: string;
  retrieval_mode: string;
  embedding_model: string;
  chunking_strategy: string;
  jd_quality?: "ok" | "weak"; // NEW
  structured_skills?: string[]; // NEW
};
