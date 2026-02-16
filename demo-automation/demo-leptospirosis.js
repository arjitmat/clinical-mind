/**
 * Clinical Mind - Automated Demo Script
 * Case: Leptospirosis (Weil's Disease)
 *
 * This script runs autonomously to demonstrate all features of Clinical Mind
 * Perfect for hackathon presentations - consistent, professional, no fumbling
 */

const puppeteer = require('puppeteer');

// Timing constants (adjust for pacing)
const TYPING_DELAY = 80; // ms between keystrokes (looks natural)
const READ_DELAY = 3000; // Time to "read" responses
const SHORT_PAUSE = 1500; // Between actions
const LONG_PAUSE = 4000; // After important moments

async function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function typeMessage(page, message) {
  // Click the input field
  await page.click('textarea[placeholder*="Type your message"]');
  await sleep(500);

  // Clear any existing text
  await page.keyboard.down('Control');
  await page.keyboard.press('A');
  await page.keyboard.up('Control');

  // Type the message with realistic speed
  await page.type('textarea[placeholder*="Type your message"]', message, { delay: TYPING_DELAY });
  await sleep(500);

  // Press Enter to send
  await page.keyboard.press('Enter');
}

async function waitForResponse(page, timeout = 30000) {
  // Wait for loading to complete (no loading states visible)
  await page.waitForFunction(
    () => !document.querySelector('.animate-pulse'),
    { timeout }
  );
  await sleep(READ_DELAY);
}

async function scrollToBottom(page) {
  await page.evaluate(() => {
    const chatContainer = document.querySelector('[class*="overflow-y-auto"]');
    if (chatContainer) {
      chatContainer.scrollTop = chatContainer.scrollHeight;
    }
  });
}

async function clickActionButton(page, buttonText) {
  // Find and click action button by text
  await page.evaluate((text) => {
    const buttons = Array.from(document.querySelectorAll('button'));
    const button = buttons.find(btn => btn.textContent.includes(text));
    if (button) button.click();
  }, buttonText);
}

async function runDemo() {
  console.log('🚀 Starting Clinical Mind Demo - Leptospirosis Case');
  console.log('📹 Please start screen recording now...\n');

  // Launch browser
  const browser = await puppeteer.launch({
    headless: false, // Shows the browser
    defaultViewport: { width: 1920, height: 1080 },
    args: [
      '--window-size=1920,1080',
      '--no-sandbox',
      '--disable-setuid-sandbox',
      '--disable-blink-features=AutomationControlled'
    ]
  });

  const page = await browser.newPage();

  try {
    // 1. Navigate to main page (NOT demo page - showing real app)
    console.log('📍 Step 1: Opening Clinical Mind...');
    await page.goto('http://localhost:3000', { waitUntil: 'networkidle2' });
    await sleep(LONG_PAUSE);

    // 2. Click "Start Simulation" on landing page
    console.log('📍 Step 2: Starting simulation...');
    await page.click('a[href="/simulation"]');
    await page.waitForNavigation({ waitUntil: 'networkidle2' });
    await sleep(SHORT_PAUSE);

    // 3. Select difficulty level (Intermediate)
    console.log('📍 Step 3: Selecting difficulty - Intermediate...');
    await page.waitForSelector('button:has-text("Intermediate")', { timeout: 10000 });
    await page.click('button:has-text("Intermediate")');
    await sleep(SHORT_PAUSE);

    // 4. Wait for case generation (shows loading state)
    console.log('📍 Step 4: Generating case...');
    await sleep(5000); // Generation time

    // 5. Wait for agent initialization
    console.log('📍 Step 5: Initializing medical team (this takes 2-3 minutes)...');
    console.log('   - Building patient knowledge...');
    console.log('   - Building nurse knowledge...');
    console.log('   - Building family knowledge...');
    console.log('   - Building lab tech knowledge...');
    console.log('   - Building senior doctor knowledge...');

    // Wait for chat interface to appear (agents ready)
    await page.waitForSelector('textarea[placeholder*="Type your message"]', { timeout: 240000 });
    console.log('✅ Medical team ready!\n');
    await sleep(LONG_PAUSE);

    // Scroll to see initial messages
    await scrollToBottom(page);
    await sleep(READ_DELAY);

    // === DEMO CONVERSATION BEGINS ===
    console.log('🎬 Starting medical consultation...\n');

    // 6. Initial patient interaction
    console.log('👨‍⚕️ Doctor: Asking about symptoms...');
    await typeMessage(page, "Namaste, can you tell me what brought you to the hospital today?");
    await waitForResponse(page);
    await scrollToBottom(page);
    await sleep(READ_DELAY);

    // 7. Ask about fever pattern
    console.log('👨‍⚕️ Doctor: Inquiring about fever...');
    await typeMessage(page, "Tell me more about your fever. When did it start?");
    await waitForResponse(page);
    await scrollToBottom(page);
    await sleep(READ_DELAY);

    // 8. Check vitals
    console.log('👨‍⚕️ Doctor: Checking vital signs...');
    await clickActionButton(page, "Ask Nurse");
    await sleep(SHORT_PAUSE);
    await typeMessage(page, "Nurse Priya, what are the current vital signs?");
    await waitForResponse(page);
    await scrollToBottom(page);
    await sleep(READ_DELAY);

    // Show vitals panel changes (highlighting critical values)
    console.log('📊 Vitals: BP 85/50 (LOW), HR 132 (HIGH), Temp 39.2°C');
    await sleep(LONG_PAUSE);

    // 9. Physical examination
    console.log('👨‍⚕️ Doctor: Performing physical examination...');
    await clickActionButton(page, "Examine Patient");
    await sleep(SHORT_PAUSE);
    await typeMessage(page, "Let me examine your abdomen for tenderness");
    await waitForResponse(page);
    await scrollToBottom(page);

    // Examination modal should appear
    await sleep(READ_DELAY);

    // 10. Talk to family
    console.log('👨‍⚕️ Doctor: Gathering history from family...');
    await clickActionButton(page, "Talk to Family");
    await sleep(SHORT_PAUSE);
    await typeMessage(page, "Can you tell me about his work and recent activities?");
    await waitForResponse(page);
    await scrollToBottom(page);
    await sleep(READ_DELAY);

    // 11. Order investigations
    console.log('👨‍⚕️ Doctor: Ordering blood tests...');
    await clickActionButton(page, "Order Investigation");
    await sleep(SHORT_PAUSE);
    await typeMessage(page, "Order CBC, LFT, RFT, and Leptospira IgM ELISA urgently");
    await waitForResponse(page);
    await scrollToBottom(page);
    await sleep(READ_DELAY);

    // 12. Team huddle for differential diagnosis
    console.log('👨‍⚕️ Doctor: Calling team huddle...');
    await clickActionButton(page, "Team Huddle");
    await sleep(SHORT_PAUSE);
    await typeMessage(page, "Let's discuss the differential diagnosis. Patient has fever, jaundice, and kidney involvement.");
    await waitForResponse(page);
    await scrollToBottom(page);
    await sleep(LONG_PAUSE);

    // 13. Check investigation results (after time passes)
    console.log('⏰ Waiting for lab results...');
    await sleep(5000);

    console.log('👨‍⚕️ Doctor: Checking lab results...');
    await clickActionButton(page, "Ask Lab Tech");
    await sleep(SHORT_PAUSE);
    await typeMessage(page, "Ramesh, are the urgent lab results ready?");
    await waitForResponse(page);
    await scrollToBottom(page);
    await sleep(READ_DELAY);

    // 14. Start treatment
    console.log('👨‍⚕️ Doctor: Initiating treatment...');
    await clickActionButton(page, "Order Treatment");
    await sleep(SHORT_PAUSE);
    await typeMessage(page, "Start IV Crystalline Penicillin 1.5 MU Q6H and aggressive fluid resuscitation");
    await waitForResponse(page);
    await scrollToBottom(page);
    await sleep(READ_DELAY);

    // 15. Consult senior doctor for guidance
    console.log('👨‍⚕️ Doctor: Consulting senior physician...');
    await clickActionButton(page, "Consult Senior");
    await sleep(SHORT_PAUSE);
    await typeMessage(page, "Dr. Sharma, patient has confirmed leptospirosis with multi-organ involvement. What else should we monitor?");
    await waitForResponse(page);
    await scrollToBottom(page);
    await sleep(LONG_PAUSE);

    // 16. Show deterioration and urgency
    console.log('⚠️ Patient deteriorating - demonstrating urgency features...');
    await sleep(3000);

    // 17. Final diagnosis
    console.log('👨‍⚕️ Doctor: Confirming diagnosis...');
    await typeMessage(page, "Based on clinical findings and lab results, diagnosis is Weil's disease - severe leptospirosis with hepatorenal syndrome");
    await waitForResponse(page);
    await scrollToBottom(page);
    await sleep(LONG_PAUSE);

    // === END OF DEMO ===
    console.log('\n✅ Demo completed successfully!');
    console.log('📹 You can stop recording now.');
    console.log('\n🎯 Key Features Demonstrated:');
    console.log('   ✓ Multi-agent interactions (5 agents)');
    console.log('   ✓ Hinglish patient responses');
    console.log('   ✓ Real-time vital signs monitoring');
    console.log('   ✓ Physical examination system');
    console.log('   ✓ Investigation ordering & results');
    console.log('   ✓ Treatment management');
    console.log('   ✓ Team collaboration (huddle)');
    console.log('   ✓ Educational guidance from senior doctor');
    console.log('   ✓ Patient deterioration mechanics');
    console.log('   ✓ Context-aware suggested questions');

    // Keep browser open for 10 seconds to show final state
    await sleep(10000);

  } catch (error) {
    console.error('❌ Demo error:', error);
  } finally {
    await browser.close();
  }
}

// Run the demo
runDemo().catch(console.error);