/* Scripted E2E smoke test + screenshot capture for the PhishForge Console,
 * run against the real dev servers (backend :8000 demo mode, frontend
 * :5173). Not part of the Vitest unit suite -- a standalone Playwright
 * script, per docs/DECISIONS.md (installed cleanly, used for both the E2E
 * smoke pass and the visual screenshot review). */
const { chromium } = require('playwright')
const fs = require('fs')
const path = require('path')

const BASE = 'http://127.0.0.1:5173'
const OUT_DIR = path.join(__dirname, 'screenshots')
fs.mkdirSync(OUT_DIR, { recursive: true })

const failures = []
function check(name, cond) {
  if (!cond) failures.push(name)
  console.log(`${cond ? 'PASS' : 'FAIL'} - ${name}`)
}

async function main() {
  const browser = await chromium.launch()

  // ---- Functional smoke: each of the 4 demo scripts via the real UI ----
  {
    const page = await browser.newPage({ viewport: { width: 1440, height: 900 } })
    const consoleErrors = []
    page.on('console', (msg) => {
      if (msg.type() === 'error') consoleErrors.push(msg.text())
    })
    await page.goto(BASE + '/')
    await page.waitForSelector('h1:has-text("Studio")')

    // Fill minimal required fields
    await page.fill('textarea', 'Playwright smoke-test org, 200 employees.')
    await page.click('button:has-text("+ urgency")')

    // Exact-text match (quoted) is required: the scenario_type dropdown
    // already renders "Password Alert", which a plain substring match on
    // "Pass" would wrongly match before any run even starts.
    const scripts = [
      { label: 'first_pass', expect: 'Pass' },
      { label: 'revise_pass', expect: 'Pass' },
      { label: 'safety_reject', expect: 'Rejected (unsafe)' },
      { label: 'plateau', expect: 'Failed to converge' },
    ]

    const demoSelect = page.locator('select').filter({ has: page.locator('option', { hasText: 'Auto (based on difficulty)' }) })

    for (const s of scripts) {
      await demoSelect.selectOption({ label: labelFor(s.label) })
      await page.click('button:has-text("Run scenario")')
      await page.waitForSelector(`text="${s.expect}"`, { timeout: 20000 })
      check(`Studio run (${s.label}) shows "${s.expect}"`, true)
    }

    check('No console errors during Studio runs', consoleErrors.length === 0)
    if (consoleErrors.length) console.log('Console errors:', consoleErrors)

    // Convergence chart present for revise_pass's two-iteration run (last run was plateau, 3 iterations)
    const chart = await page.locator('[role="img"][aria-label*="Quality score by iteration"]').count()
    check('Convergence chart rendered', chart > 0)

    await page.close()
  }

  // ---- Runs page ----
  {
    const page = await browser.newPage({ viewport: { width: 1440, height: 900 } })
    await page.goto(BASE + '/runs')
    await page.waitForSelector('table')
    const rowCount = await page.locator('table tbody tr').count()
    check('Runs table lists rows', rowCount > 0)
    await page.close()
  }

  // ---- Dashboard page ----
  {
    const page = await browser.newPage({ viewport: { width: 1440, height: 900 } })
    await page.goto(BASE + '/dashboard')
    await page.waitForSelector('text=Total runs')
    const kpi = await page.locator('text=Total runs').count()
    check('Dashboard KPI cards render', kpi > 0)
    await page.close()
  }

  // ---- Settings page ----
  {
    const page = await browser.newPage({ viewport: { width: 1440, height: 900 } })
    await page.goto(BASE + '/settings')
    await page.waitForSelector('text=Provider status')
    const rubric = await page.locator('text=Level 1').count()
    check('Settings shows difficulty rubric', rubric > 0)
    await page.close()
  }

  // ---- Screenshots: every page, both themes, desktop + tablet ----
  const pages = [
    { path: '/', name: 'studio' },
    { path: '/runs', name: 'runs' },
    { path: '/dashboard', name: 'dashboard' },
    { path: '/settings', name: 'settings' },
  ]
  const viewports = [
    { name: 'desktop', width: 1440, height: 900 },
    { name: 'tablet', width: 820, height: 1180 },
  ]
  const themes = ['light', 'dark']

  for (const vp of viewports) {
    for (const theme of themes) {
      const page = await browser.newPage({ viewport: { width: vp.width, height: vp.height } })
      await page.emulateMedia({ colorScheme: theme })
      for (const p of pages) {
        await page.goto(BASE + p.path)
        await page.waitForTimeout(1500) // let chart entry animations finish before capturing
        const file = path.join(OUT_DIR, `${p.name}-${vp.name}-${theme}.png`)
        await page.screenshot({ path: file, fullPage: true })
        console.log('Screenshot saved:', file)
      }
      await page.close()
    }
  }

  await browser.close()

  console.log('\n=== SUMMARY ===')
  console.log(`${failures.length === 0 ? 'ALL CHECKS PASSED' : `${failures.length} FAILURE(S)`}`)
  if (failures.length) {
    console.log(failures.join('\n'))
    process.exit(1)
  }
}

function labelFor(key) {
  return (
    {
      first_pass: 'First-pass PASS',
      revise_pass: 'REVISE → PASS',
      safety_reject: 'Safety-gate rejection',
      plateau: 'Plateau / FAILED_TO_CONVERGE',
    }[key] || key
  )
}

main().catch((e) => {
  console.error(e)
  process.exit(1)
})
