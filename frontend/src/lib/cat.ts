export function getCatStage(totalScore: number): number {
  if (totalScore <= 50) return 1;
  if (totalScore <= 150) return 2;
  if (totalScore <= 300) return 3;
  return 4;
}

export function getCatImage(stage: number): string {
  if (stage === 1) return "/images/cat-stage-1.png";
  if (stage === 2) return "/images/cat-stage-2.png";
  if (stage === 3) return "/images/cat-stage-3.png";
  return "/images/cat-stage-4.png";
}

export function stageLabel(stage: number): string {
  switch (stage) {
    case 1:
      return "阶段 1 · 幼猫";
    case 2:
      return "阶段 2 · 少年猫";
    case 3:
      return "阶段 3 · 强壮猫";
    default:
      return "阶段 4 · 终极猫";
  }
}

export function nextStageDiff(totalScore: number): number {
  if (totalScore <= 50) return 51 - totalScore;
  if (totalScore <= 150) return 151 - totalScore;
  if (totalScore <= 300) return 301 - totalScore;
  return 0;
}
