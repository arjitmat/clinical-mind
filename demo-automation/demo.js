/**
 * Clinical Mind - Automated Demo Script (Medical Student Version)
 *
 * Showcases the educational medical simulation with 5 AI agents
 * Perfect for hackathon recording - demonstrates multi-agent orchestration
 */

const puppeteer = require('puppeteer');

// Timing constants
const TYPING_DELAY = 70;
const READ_DELAY = 3000;
const SHORT_PAUSE = 1500;
const LONG_PAUSE = 4000;

async function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function typeMessage(page, message) {
  // Try multiple selectors for the input field
  const inputSelectors = [
    'input[type="text"][placeholder]',
    'textarea[placeholder]',
    '.flex-1.p-2\\.5.rounded-lg',
    'input.flex-1',
    '[role="textbox"]'
  ];

  let inputFound = false;
  let activeSelector = null;

  // Find which selector works
  for (const selector of inputSelectors) {
    try {
      await page.waitForSelector(selector, { timeout: 2000, visible: true });
      const isVisible = await page.evaluate((sel) => {
        const el = document.querySelector(sel);
        return el && el.offsetParent !== null;
      }, selector);

      if (isVisible) {
        activeSelector = selector;
        inputFound = true;
        break;
      }
    } catch {
      continue;
    }
  }

  if (!inputFound) {
    console.log('⚠️ Could not find input field, skipping message');
    return;
  }

  // Click to focus
  await page.click(activeSelector);
  await sleep(300);

  // Clear any existing text
  await page.evaluate((selector) => {
    const input = document.querySelector(selector);
    if (input) {
      input.value = '';
      input.textContent = '';
    }
  }, activeSelector);

  // Type message
  await page.type(activeSelector, message, { delay: TYPING_DELAY });
  await sleep(300);

  // Send message (try Enter, then look for Send button)
  await page.keyboard.press('Enter');

  // Alternative: click Send button if Enter doesn't work
  const sendClicked = await page.evaluate(() => {
    const buttons = Array.from(document.querySelectorAll('button'));
    const sendBtn = buttons.find(btn =>
      btn.textContent.toLowerCase() === 'send' &&
      !btn.disabled
    );
    if (sendBtn) {
      sendBtn.click();
      return true;
    }
    return false;
  });

  if (sendClicked) {
    console.log('   (Used Send button)');
  }
}

async function waitForResponse(page, timeout = 30000) {
  // Wait for typing indicator to disappear
  try {
    await page.waitForFunction(
      () => {
        const typingElements = document.querySelectorAll('[class*="typing"], [class*="loading"], .animate-pulse');
        return typingElements.length === 0;
      },
      { timeout }
    );
  } catch (e) {
    console.log('Response timeout - continuing...');
  }
  await sleep(READ_DELAY);
}

async function scrollChat(page) {
  await page.evaluate(() => {
    const chatContainers = document.querySelectorAll('[class*="overflow-y-auto"]');
    chatContainers.forEach(container => {
      container.scrollTop = container.scrollHeight;
    });
  });
}

async function clickButton(page, buttonText) {
  await page.evaluate((text) => {
    const buttons = Array.from(document.querySelectorAll('button'));
    const button = buttons.find(btn =>
      btn.textContent.toLowerCase().includes(text.toLowerCase())
    );
    if (button) {
      button.click();
      return true;
    }
    return false;
  }, buttonText);
}

async function clickActionTab(page, actionName) {
  // Try to click the action tab/button
  const clicked = await page.evaluate((name) => {
    // First try exact match in small action buttons
    const actionButtons = document.querySelectorAll('.flex.flex-wrap.gap-1 button');
    for (const btn of actionButtons) {
      if (btn.textContent.trim() === name || btn.textContent.includes(name)) {
        btn.click();
        console.log(`Clicked action tab: ${name}`);
        return true;
      }
    }

    // Then try any button with matching text
    const allButtons = Array.from(document.querySelectorAll('button'));
    const button = allButtons.find(btn =>
      btn.textContent === name || btn.textContent.includes(name)
    );
    if (button) {
      button.click();
      console.log(`Clicked button: ${name}`);
      return true;
    }

    console.log(`Could not find action: ${name}`);
    return false;
  }, actionName);

  if (!clicked) {
    console.log(`⚠️ Could not click action tab: ${actionName}`);
  }

  await sleep(SHORT_PAUSE);
}

async function runDemo() {
  console.log('🚀 Starting Clinical Mind Automated Demo');
  console.log('📹 Start your screen recording software now!');
  console.log('⏰ Starting in 5 seconds...\n');
  await sleep(5000);

  let browser;
  let retries = 3;

  // Retry logic for browser launch
  while (retries > 0) {
    try {
      browser = await puppeteer.launch({
        headless: false,
        defaultViewport: { width: 1920, height: 1080 },
        args: [
          '--window-size=1920,1080',
          '--no-sandbox',
          '--disable-setuid-sandbox',
          '--disable-dev-shm-usage',
          '--disable-accelerated-2d-canvas',
          '--no-first-run',
          '--no-zygote',
          '--disable-gpu',
          '--disable-web-security',
          '--disable-features=IsolateOrigins,site-per-process'
        ],
        ignoreHTTPSErrors: true,
        dumpio: false,
        timeout: 60000,
        protocolTimeout: 60000
      });

      // If browser launched successfully, break the retry loop
      console.log('✅ Browser launched successfully');
      break;
    } catch (error) {
      retries--;
      console.log(`⚠️ Browser launch failed. Retries remaining: ${retries}`);
      if (retries === 0) {
        throw new Error('Failed to launch browser after 3 attempts: ' + error.message);
      }
      // Wait before retrying
      await sleep(2000);
    }
  }

  const page = await browser.newPage();

  try {
    // 1. Navigate to demo page
    console.log('📍 Opening Clinical Mind Demo...');
    await page.goto('http://localhost:3000/demo', { waitUntil: 'networkidle2' });
    await sleep(LONG_PAUSE);

    // 2. Fill Student Profile
    console.log('📍 Setting up medical student profile...');

    // Enter student name
    await page.waitForSelector('input[placeholder*="Enter your name"]', { timeout: 10000 });
    await page.type('input[placeholder*="Enter your name"]', 'Arjun Sharma', { delay: TYPING_DELAY });
    await sleep(SHORT_PAUSE);

    // Select MBBS Final Year (advanced student)
    console.log('   Selecting: MBBS Final Year');
    await page.evaluate(() => {
      const buttons = Array.from(document.querySelectorAll('button'));
      const finalYearBtn = buttons.find(btn => btn.textContent.includes('MBBS Final Year'));
      if (finalYearBtn) finalYearBtn.click();
    });
    await sleep(SHORT_PAUSE);

    // Click Continue to Cases
    await clickButton(page, 'Continue to Cases');
    await sleep(LONG_PAUSE);

    // 3. Select Case
    console.log('📍 Selecting case: Dengue Fever (Infectious Disease)...');
    await page.waitForSelector('.grid', { timeout: 10000 });
    await sleep(SHORT_PAUSE); // Let the page stabilize

    // Click on the "Start This Case" button in the second card
    const caseSelected = await page.evaluate(() => {
      const cards = document.querySelectorAll('[class*="Card"]');
      console.log(`Found ${cards.length} case cards`);

      if (cards.length >= 2) {
        const secondCard = cards[1];
        // Look for the "Start This Case" button within the card
        const button = secondCard.querySelector('button');
        if (button && button.textContent.includes('Start This Case')) {
          console.log('Clicking "Start This Case" button');
          button.click();
          return true;
        } else {
          // Fallback: click the card itself
          console.log('Clicking card directly');
          secondCard.click();
          return true;
        }
      }
      return false;
    });

    if (!caseSelected) {
      console.log('⚠️ Could not find case cards, trying alternative selector...');
      // Alternative: click by text content
      await clickButton(page, 'Start This Case');
    }

    // 4. Wait for navigation to case interface
    console.log('📍 Loading case interface...');

    // Wait for URL change or new page content
    await Promise.race([
      page.waitForNavigation({ waitUntil: 'networkidle0', timeout: 30000 }),
      page.waitForSelector('[class*="Hospital Ward"]', { timeout: 30000 }),
      sleep(5000) // Fallback timeout
    ]).catch(() => {
      console.log('Navigation completed or timed out, continuing...');
    });

    await sleep(LONG_PAUSE);

    // 5. Wait for agents to initialize
    console.log('⏳ Initializing medical team (2-3 minutes)...');
    console.log('   🏥 5 AI agents are learning about this case:');
    console.log('   - Patient (with symptoms)');
    console.log('   - Family member (Hindi/English responses)');
    console.log('   - Nurse Priya (vitals monitoring)');
    console.log('   - Lab Tech Ramesh (investigations)');
    console.log('   - Dr. Sharma (senior guidance)');

    // Wait for initialization to complete (checking multiple indicators)
    console.log('   Waiting for agents to be ready...');

    // First check if there's an initialization overlay
    const hasInitOverlay = await page.evaluate(() => {
      const overlay = document.querySelector('.absolute.inset-0.bg-cream-white');
      const loadingText = document.querySelector('[class*="Preparing Hospital Ward"]');
      return !!(overlay || loadingText);
    });

    if (hasInitOverlay) {
      console.log('   Initialization overlay detected, waiting for completion...');
      // Wait for the overlay to disappear
      await page.waitForFunction(
        () => {
          const loadingOverlay = document.querySelector('[class*="Preparing Hospital Ward"]');
          const initOverlay = document.querySelector('.absolute.inset-0.bg-cream-white');
          const spinners = document.querySelectorAll('.animate-pulse, .animate-spin');
          return !loadingOverlay && !initOverlay && spinners.length === 0;
        },
        { timeout: 240000 } // 4 minutes max
      ).catch(() => {
        console.log('   Initialization timeout, proceeding anyway...');
      });
    } else {
      console.log('   No initialization overlay, agents might be pre-loaded for demo');
      await sleep(5000); // Give it some time anyway
    }

    // Wait for chat input to be ready (with multiple selectors)
    console.log('   Looking for chat interface...');
    const inputFound = await Promise.race([
      page.waitForSelector('input[type="text"][placeholder]', {
        visible: true,
        timeout: 30000
      }).then(() => true),
      page.waitForSelector('textarea[placeholder]', {
        visible: true,
        timeout: 30000
      }).then(() => true),
      page.waitForSelector('.flex-1.p-2\\.5.rounded-lg', {
        visible: true,
        timeout: 30000
      }).then(() => true)
    ]).catch(() => false);

    if (!inputFound) {
      console.log('⚠️ Chat input not found, but continuing with demo...');
      // Take a screenshot to debug
      await page.screenshot({ path: 'demo-debug.png' });
      console.log('   Screenshot saved as demo-debug.png');
    }

    console.log('✅ Medical team ready!\n');
    await sleep(LONG_PAUSE);
    await scrollChat(page);

    // === MEDICAL STUDENT CONSULTATION FLOW ===
    console.log('🎬 Beginning medical consultation as MBBS student...\n');

    // 1. Initial greeting to patient
    console.log('🧑‍🎓 [1/18] Greeting patient...');
    await clickActionTab(page, 'Patient');
    await typeMessage(page, "Hello, I'm Arjun, a final year medical student. What brought you to the hospital today?");
    await waitForResponse(page);
    await scrollChat(page);

    // 2. History taking
    console.log('🧑‍🎓 [2/18] Taking detailed history...');
    await typeMessage(page, "When did the fever start? Any other symptoms like headache or body pain?");
    await waitForResponse(page);
    await scrollChat(page);

    // 3. Ask about rash
    console.log('🧑‍🎓 [3/18] Checking for specific symptoms...');
    await typeMessage(page, "Have you noticed any rash on your body? Any bleeding from gums or nose?");
    await waitForResponse(page);
    await scrollChat(page);

    // 4. Talk to family for context
    console.log('🧑‍🎓 [4/18] Getting history from family...');
    await clickActionTab(page, 'Family');
    await typeMessage(page, "Can you tell me about the patient's symptoms over the past few days?");
    await waitForResponse(page);
    await scrollChat(page);

    // 5. Check vitals with nurse
    console.log('🧑‍🎓 [5/18] Checking vital signs...');
    await clickActionTab(page, 'Nurse');
    await typeMessage(page, "Nurse Priya, can you please report the current vital signs?");
    await waitForResponse(page);
    await scrollChat(page);

    console.log('   📊 Analyzing vitals...');
    await sleep(SHORT_PAUSE);

    // 6. Consult senior for guidance
    console.log('🧑‍🎓 [6/18] Consulting senior doctor...');
    await clickActionTab(page, 'Dr. Sharma');
    await typeMessage(page, "Dr. Sharma, patient has high fever with body aches for 4 days. What should I look for?");
    await waitForResponse(page);
    await scrollChat(page);

    // 7. Physical examination
    console.log('🧑‍🎓 [7/18] Performing physical examination...');
    await clickActionTab(page, 'Examine');
    await typeMessage(page, "I want to examine for petechial rash and check tourniquet test");
    await waitForResponse(page);
    await scrollChat(page);

    // 8. Order basic investigations
    console.log('🧑‍🎓 [8/18] Ordering investigations...');
    await clickActionTab(page, 'Investigate');
    await typeMessage(page, "Please order CBC with platelet count, NS1 antigen test, and dengue serology");
    await waitForResponse(page);
    await scrollChat(page);

    // 9. Team huddle for differential
    console.log('🧑‍🎓 [9/18] Team discussion...');
    await clickActionTab(page, 'Huddle');
    await typeMessage(page, "Team, let's discuss the differential diagnosis. Could this be dengue fever?");
    await waitForResponse(page);
    await scrollChat(page);

    // 10. Check investigation status
    console.log('🧑‍🎓 [10/18] Checking lab results...');
    await clickActionTab(page, 'Lab');
    await typeMessage(page, "Ramesh, are the CBC and dengue test results ready?");
    await waitForResponse(page);
    await scrollChat(page);

    // 11. Monitor patient condition
    console.log('🧑‍🎓 [11/18] Monitoring patient...');
    await clickActionTab(page, 'Nurse');
    await typeMessage(page, "Please monitor urine output and watch for warning signs of dengue");
    await waitForResponse(page);
    await scrollChat(page);

    // 12. Start treatment
    console.log('🧑‍🎓 [12/18] Initiating treatment...');
    await clickActionTab(page, 'Treat');
    await typeMessage(page, "Start IV fluids - NS 500ml over 4 hours, and paracetamol for fever");
    await waitForResponse(page);
    await scrollChat(page);

    // 13. Reassess with patient
    console.log('🧑‍🎓 [13/18] Reassessing patient...');
    await clickActionTab(page, 'Patient');
    await typeMessage(page, "How are you feeling now? Any abdominal pain or vomiting?");
    await waitForResponse(page);
    await scrollChat(page);

    // 14. Check vitals trend
    console.log('🧑‍🎓 [14/18] Checking vitals trend...');
    await clickActionTab(page, 'Nurse');
    await typeMessage(page, "What's the trend of blood pressure and platelet count?");
    await waitForResponse(page);
    await scrollChat(page);

    // 15. Discuss management with senior
    console.log('🧑‍🎓 [15/18] Discussing management plan...');
    await clickActionTab(page, 'Dr. Sharma');
    await typeMessage(page, "Dr. Sharma, platelets are dropping. Should we admit for monitoring?");
    await waitForResponse(page);
    await scrollChat(page);

    // 16. Patient education
    console.log('🧑‍🎓 [16/18] Educating patient...');
    await clickActionTab(page, 'Patient');
    await typeMessage(page, "You have dengue fever. We'll monitor you closely. Stay hydrated and rest.");
    await waitForResponse(page);
    await scrollChat(page);

    // 17. Family counseling
    console.log('🧑‍🎓 [17/18] Counseling family...');
    await clickActionTab(page, 'Family');
    await typeMessage(page, "Please ensure mosquito protection at home. Bring patient back if warning signs appear.");
    await waitForResponse(page);
    await scrollChat(page);

    // 18. Final assessment
    console.log('🧑‍🎓 [18/18] Final clinical reasoning...');
    await clickActionTab(page, 'Dr. Sharma');
    await typeMessage(page, "Based on clinical findings and low platelets, diagnosis is dengue fever with warning signs");
    await waitForResponse(page);
    await scrollChat(page);

    console.log('\n✅ Demo completed successfully!');
    console.log('📹 Recording complete - you can stop now.\n');

    console.log('🎯 Features Demonstrated:');
    console.log('   ✓ Student profile & level selection');
    console.log('   ✓ 5 AI agents with specialized roles');
    console.log('   ✓ Authentic Hindi/English patient responses');
    console.log('   ✓ Real-time vital signs monitoring');
    console.log('   ✓ Complete clinical workflow');
    console.log('   ✓ Educational guidance from senior doctor');
    console.log('   ✓ Clinical reasoning & critical thinking');
    console.log('   ✓ Multi-agent orchestration');
    console.log('   ✓ Investigation & treatment management');
    console.log('   ✓ Patient & family counseling');

    // Keep browser open
    await sleep(10000);

  } catch (error) {
    console.error('❌ Error during demo:', error.message);
    console.log('💡 Tips:');
    console.log('   1. Make sure the app is running on localhost:3000');
    console.log('   2. Check that /demo page is accessible');
    console.log('   3. Ensure all components are loaded');
  } finally {
    console.log('\n🔚 Closing browser...');
    await browser.close();
  }
}

// Run demo with better error handling
runDemo().catch((error) => {
  console.error('❌ Error during demo:', error.message);
  if (error.message.includes('WebSocket') || error.message.includes('socket hang up')) {
    console.log('\n💡 WebSocket Connection Error - Troubleshooting tips:');
    console.log('   1. Try running the demo again (WebSocket errors are often temporary)');
    console.log('   2. Make sure no other Chrome/Chromium processes are running');
    console.log('   3. Kill any zombie Chrome processes: killall "Google Chrome"');
    console.log('   4. Clear Puppeteer cache: rm -rf ~/.cache/puppeteer');
    console.log('   5. Re-run setup: ./setup.sh');
  }
  process.exit(1);
});