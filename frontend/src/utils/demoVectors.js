/**
 * Real CICIDS2017 scaled feature vectors (78-dim) for reliable UI demos.
 * Sourced from dataset/CICIDS2017/processed/train_test_data.pkl — not random noise.
 */
import demoVectors from "./demoVectors.json";

export const DEMO_FEATURE_VECTORS = demoVectors;

export function getDemoVectorByLabel(label) {
  return DEMO_FEATURE_VECTORS.find((row) => row.label === label) || null;
}

/** Prefer non-BENIGN samples for “Demo Attack”. */
export function pickDemoAttackVector() {
  const attacks = DEMO_FEATURE_VECTORS.filter((row) => row.label !== "BENIGN");
  if (!attacks.length) return DEMO_FEATURE_VECTORS[0];
  return attacks[Math.floor(Math.random() * attacks.length)];
}

export function pickDemoBenignVector() {
  return (
    DEMO_FEATURE_VECTORS.find((row) => row.label === "BENIGN") ||
    DEMO_FEATURE_VECTORS[0]
  );
}

/** Random real vector (benign or attack) for “Generate features”. */
export function pickAnyDemoVector() {
  return DEMO_FEATURE_VECTORS[
    Math.floor(Math.random() * DEMO_FEATURE_VECTORS.length)
  ];
}
