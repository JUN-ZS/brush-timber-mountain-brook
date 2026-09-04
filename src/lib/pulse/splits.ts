export type SplitName = "TRAIN" | "VALIDATION" | "CRISIS_STUDY" | "UNPROVEN_OOS";

export function assignSplit(date: string): SplitName {
  if (date < "2016-01-01") return "TRAIN";
  if (date < "2020-01-01") return "VALIDATION";
  if (date < "2023-01-01") return "CRISIS_STUDY";
  return "UNPROVEN_OOS";
}
