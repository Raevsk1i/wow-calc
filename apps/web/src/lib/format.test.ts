import { describe, expect, it } from "vitest";

import { formatDps } from "@/lib/api";

describe("formatDps", () => {
  it("formats integers with grouping", () => {
    expect(formatDps(133261.4)).toMatch(/133/);
  });
});
