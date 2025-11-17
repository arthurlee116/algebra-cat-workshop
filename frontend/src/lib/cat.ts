export function getCatStage(catScore: number): number {
  if (catScore <= 50) return 1;
  if (catScore <= 150) return 2;
  if (catScore <= 300) return 3;
  return 4;
}

export function getCatImage(stage: number): string {
  if (stage === 1) return "/images/cat-stage-1.gif";
  if (stage === 2) return "/images/cat-stage-2.gif";
  if (stage === 3) return "/images/cat-stage-3.gif";
  return "/images/cat-stage-4.gif";
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

export function nextStageDiff(catScore: number): number {
  if (catScore <= 50) return 51 - catScore;
  if (catScore <= 150) return 151 - catScore;
  if (catScore <= 300) return 301 - catScore;
  return 0;
}
