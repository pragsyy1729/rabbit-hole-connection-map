export interface PathStep {
  step: number;
  concept: string;
  wikipedia_extract: string;
  wikipedia_url: string;
  connection_to_next: string | null;
}

export interface RabbitHole {
  id: string;
  created_at: string;
  concept_a: string;
  concept_b: string;
  steps: PathStep[];
}
