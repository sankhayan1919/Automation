const { chromium } = require('playwright');
const PDFDocument = require('pdf-lib').PDFDocument;
const fs = require('fs');

(async () => {
    const browser = await chromium.launch({ headless: false, args: ['--start-maximized'] });
    const page = await browser.newPage();

    // Step 1: Log in to Instagram
    await page.goto('https://www.instagram.com/accounts/login/');
    await page.waitForSelector('input[name="username"]');
    await page.type('input[name="username"]', 'jackpage217');
    await page.type('input[name="password"]', 'jack12#');
    await page.click('button[type="submit"]');
    await page.waitForNavigation();

    // Step 2: Navigate to the target account
    await page.goto('https://www.instagram.com/blackjack2365/');

    // Step 3: Open the posts section and load all posts
    const posts = await page.$$('article a'); // Select all post links
    const pdfDoc = await PDFDocument.create();

    for (let post of posts) {
        await post.click();
        await page.waitForSelector('article'); // Wait for the post to load

        // Step 4: Expand comments and take screenshots
        const viewRepliesButton = await page.$('button[aria-label="View comments"]');
        if (viewRepliesButton) {
            await viewRepliesButton.click();
            await page.waitForTimeout(2000); // Wait for comments to load
        }

        // Zoom in slightly (using CSS transform)
        await page.evaluate(() => {
            document.body.style.transform = 'scale(1.1)';
            document.body.style.transformOrigin = 'top left';
        });

        // Take screenshot of the post and comments
        const screenshot = await page.screenshot({ fullPage: true });
        const img = await pdfDoc.addPage();
        img.drawImage(screenshot, { x: 0, y: 0, width: img.getWidth(), height: img.getHeight() });

        // Step 5: Handle carousel posts
        const carouselNextButton = await page.$('button[aria-label="Next"]');
        while (carouselNextButton) {
            await page.waitForTimeout(2000); // Wait for the next image to load
            const carouselScreenshot = await page.screenshot({ fullPage: true });
            const carouselImg = await pdfDoc.addPage();
            carouselImg.drawImage(carouselScreenshot, { x: 0, y: 0, width: carouselImg.getWidth(), height: carouselImg.getHeight() });
            await carouselNextButton.click();
            // Re-select the next button after clicking
            carouselNextButton = await page.$('button[aria-label="Next"]');
        }

        await page.click('button[aria-label="Close"]'); // Close the post
        await page.waitForTimeout(1000); // Wait before moving to the next post
    }

    // Step 6: Save screenshots to PDF
    const pdfBytes = await pdfDoc.save();
    fs.writeFileSync('posts_ss.pdf', pdfBytes);

    await browser.close();
})();
