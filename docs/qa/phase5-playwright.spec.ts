/**
 * phase5-playwright.spec.ts — Phase 5 Buyer Journey E2E spec.
 *
 * Covers all 5 buyer screens per CLAUDE.md §11 and docs/assignment.md §22 rubric.
 * Serial execution: tests share browser state so later tests build on vendors loaded
 * by earlier tests (e.g. test 3 uses the vendor loaded by test 2).
 *
 * data-testid attributes required in implementation (Plans 05-04/05-06):
 *   data-testid="gaps-panel"             — Gaps & Risks card
 *   data-testid="extraction-result"      — per-category section container
 *   data-testid="evidence-snippet"       — each EvidenceSnippet root element
 *   data-testid="comparability-matrix"   — matrix table
 *   data-testid="trace-diff"             — downgrade diff card
 *   data-testid="vendor-card-thorough"   — Thorough sample card
 *   data-testid="vendor-card-cheap"      — Cheap sample card
 *   data-testid="vendor-card-fluff"      — Fluff sample card
 */

import { BrowserContext, Page, test, expect } from "@playwright/test";

const BASE_URL = process.env.PLAYWRIGHT_BASE_URL ?? "http://localhost:3000";

test.describe.serial("Phase 5 — Buyer Journey E2E", () => {
  // Live GPT-5.4 calls (RFQ regen + per-vendor extraction + comparison) are slow
  // and latency varies run to run, so timeouts are generous.
  test.setTimeout(240_000);

  // Tests 1–6 build on each other's session state (load a vendor, then a second,
  // then compare). Playwright's per-test `page` fixture would give each test a fresh
  // context with empty sessionStorage, so the serial build-up needs ONE shared page.
  // Test 7 (empty-state) deliberately uses its own fresh context instead.
  let context: BrowserContext;
  let page: Page;

  test.beforeAll(async ({ browser }) => {
    context = await browser.newContext();
    page = await context.newPage();
  });

  test.afterAll(async () => {
    await context.close();
  });

  // Live GPT-5.4 calls (extraction, comparison) far exceed the 5s default expect timeout.
  const LIVE = { timeout: 180_000 };

  test("RFQ Overview loads committed data", async () => {
    await page.goto(`${BASE_URL}/rfq`);
    // Assert RFQ heading visible
    await expect(page.getByRole("heading", { name: /rfq/i })).toBeVisible();
    // Assert at least one line item name rendered
    await expect(page.locator('[data-testid="rfq-line-item"]').first()).toBeVisible();
    // Assert regenerate button present
    await expect(page.getByRole("button", { name: /regenerate rfq/i })).toBeVisible();
  });

  test("Vendor Input — sample load hero path (D-04)", async () => {
    await page.goto(`${BASE_URL}/input`);
    // Three sample vendor cards visible
    await expect(page.locator('[data-testid="vendor-card-thorough"]')).toBeVisible();
    await expect(page.locator('[data-testid="vendor-card-cheap"]')).toBeVisible();
    await expect(page.locator('[data-testid="vendor-card-fluff"]')).toBeVisible();
    // Load Thorough vendor — navigates to /extraction
    await page.locator('[data-testid="vendor-card-thorough"]').getByRole("button", { name: /load sample/i }).click();
    await page.waitForURL(`${BASE_URL}/extraction`, { timeout: 30_000 });
    // Wait for the live extraction to COMPLETE so it caches in sessionStorage.
    // Later /extraction visits then render from cache — faster and no repeat spend.
    await expect(page.locator('[data-testid="gaps-panel"]')).toBeVisible(LIVE);
  });

  test("Extraction Review — gaps panel visible with evidence (D-07, D-08, UI-06)", async () => {
    // Thorough was extracted + cached in the previous test → renders from cache.
    await page.goto(`${BASE_URL}/extraction`);
    await expect(page.locator('[data-testid="gaps-panel"]')).toBeVisible(LIVE);
    // At least one non-present flag badge (absence is first-class)
    await expect(page.locator('[data-testid="flag-badge"]:not([data-status="present"])').first()).toBeVisible();
    // Evidence snippet present (every shown fact carries a source span)
    await expect(page.locator('[data-testid="evidence-snippet"]').first()).toBeVisible();
    // Extraction result section
    await expect(page.locator('[data-testid="extraction-result"]')).toBeVisible();
  });

  test("Vendor Input — load second vendor (Cheap) + extract for comparison", async () => {
    await page.goto(`${BASE_URL}/input`);
    // Load Cheap — BuyerContext.setLoadedVendors must append (Plan 05-04)
    await page.locator('[data-testid="vendor-card-cheap"]').getByRole("button", { name: /load sample/i }).click();
    await page.waitForURL(`${BASE_URL}/extraction`, { timeout: 30_000 });
    // Select the 2nd vendor tab (Cheap) to trigger its extraction.
    await page.locator('[data-testid="vendor-tabs"] [role="tab"]').nth(1).click();
    // Wait until BOTH vendors are extracted + cached (comparison needs ≥2).
    await expect
      .poll(
        async () =>
          page.evaluate(
            () => Object.keys(JSON.parse(sessionStorage.getItem("extractions") || "{}")).length,
          ),
        { timeout: 120_000 },
      )
      .toBeGreaterThanOrEqual(2);
  });

  test("Comparison — comparability matrix renders + no-rank framing (D-11, D-13, D-14)", async () => {
    // Serial: ≥2 vendors in session state from tests 2 + 4
    await page.goto(`${BASE_URL}/comparison`);
    // Comparability matrix table — waits for the live comparison stream to complete
    await expect(page.locator('[data-testid="comparability-matrix"]')).toBeVisible(LIVE);
    // Attention panel first (D-12: buyer attention points surfaced before any scoring)
    await expect(page.getByText(/Needs Attention/i)).toBeVisible();
    // No-rank framing text (D-13: comparability determined in code, not a model verdict)
    await expect(page.getByText(/Comparability determined in code from evidence/i)).toBeVisible();
  });

  test("Prompt Trace — trace selector and downgrade diff visible (D-15)", async () => {
    await page.goto(`${BASE_URL}/trace`);
    // Trace file tabs visible
    await expect(page.getByRole("tab").first()).toBeVisible();
    // Downgrade diff or evidence-integrity note (D-15 reframed: verbatim-evidence integrity)
    await expect(
      page.locator("text=/Code overruled the model|code disproves|verbatim evidence/i").first()
    ).toBeVisible();
  });

  test("Extraction Review — error state is explicit not blank (D-25)", async ({ browser }) => {
    // Needs a fresh session with no vendors loaded
    const ctx2: BrowserContext = await browser.newContext();
    const page2: Page = await ctx2.newPage();
    await page2.goto(`${BASE_URL}/extraction`);
    // Must show an empty-state message, not a blank screen
    await expect(
      page2.locator("text=/no vendor|no data|upload a vendor|load a vendor/i").first()
    ).toBeVisible();
    await ctx2.close();
  });
});
