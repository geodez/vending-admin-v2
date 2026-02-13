import { test, expect } from '@playwright/test';

test('Overview chart renders correctly', async ({ page }) => {
    // Mock API responses
    await page.route('**/api/v1/auth/me*', async route => {
        await route.fulfill({ json: { id: 1, role: 'owner', username: 'test_user' } });
    });

    await page.route('**/api/v1/analytics/overview*', async route => {
        await route.fulfill({
            json: {
                total_revenue: 100000,
                total_sales: 500,
                total_gross_profit: 60000,
                total_variable_expenses: 5000,
                net_profit: 55000
            }
        });
    });

    await page.route('**/api/v1/analytics/alerts*', async route => {
        await route.fulfill({ json: { alerts: [], summary: {} } });
    });

    await page.route('**/api/v1/analytics/sales/daily*', async route => {
        await route.fulfill({
            json: [
                { date: '2024-01-01', revenue: 10000, net_profit: 5000, sales_count: 50 },
                { date: '2024-01-02', revenue: 15000, net_profit: 7000, sales_count: 70 },
                { date: '2024-01-03', revenue: 12000, net_profit: 6000, sales_count: 60 }
            ]
        });
    });

    // Navigate to overview with auth token
    await page.addInitScript(() => {
        localStorage.setItem('vending_admin_token', 'fake-test-token');
        localStorage.setItem('vending_admin_user', JSON.stringify({ id: 1, role: 'owner', username: 'test_user' }));
    });

    await page.goto('http://localhost:3000/');

    // Check for chart title - use .first() to avoid strict mode violations if multiple tabs exist
    await expect(page.locator('.ant-card-head-title').filter({ hasText: 'Динамика продаж' }).first()).toBeVisible();

    // Check for legend items (Revenue and Net Profit)
    await expect(page.getByText('Выручка').first()).toBeVisible();
    await expect(page.getByText('Чистая прибыль').first()).toBeVisible();

    // Check that the chart container exists
    const chart = page.locator('.recharts-responsive-container').first();
    await expect(chart).toBeVisible();
});
