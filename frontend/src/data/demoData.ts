import { type AgentMessageData } from '../components/case';

export interface DemoCase {
  id: string;
  title: string;
  description: string;
  specialty: string;
  difficulty: string;
  patient: {
    age: number;
    gender: string;
    location: string;
  };
  chief_complaint: string;
  initial_presentation: string;
  vital_signs: {
    bp: string;
    hr: number;
    rr: number;
    temp: number;
    spo2: number;
  };
  stages: Array<{
    stage: string;
    info: string;
  }>;
  diagnosis: string;
  learning_points: string[];
  script: {
    questions: string[];
    initialMessages: AgentMessageData[];
    responses: Record<string, AgentMessageData[]>;
  };
}

// Case 1: Acute Myocardial Infarction (Classic presentation for demo)
const miCase: DemoCase = {
  id: 'demo-mi-001',
  title: 'Acute ST-Elevation Myocardial Infarction',
  description: 'Classic heart attack presentation - perfect for demonstrating critical decision making',
  specialty: 'Cardiology',
  difficulty: 'intermediate',
  patient: {
    age: 55,
    gender: 'Male',
    location: 'Mumbai',
  },
  chief_complaint: 'Severe chest pain for 2 hours',
  initial_presentation: '55-year-old male businessman presents with crushing central chest pain radiating to left arm, started 2 hours ago while climbing stairs. Associated with profuse sweating, nausea. Known diabetic, smoker.',
  vital_signs: {
    bp: '90/60',
    hr: 110,
    rr: 24,
    temp: 37.2,
    spo2: 94,
  },
  stages: [
    {
      stage: 'history',
      info: 'Pain started suddenly 2 hours ago, 9/10 severity, crushing/squeezing nature. Radiates to left arm and jaw. Associated with profuse sweating, nausea, feeling of impending doom. History of diabetes (10 years), hypertension (5 years), smoking (20 pack-years). Father died of heart attack at 60. Takes metformin, amlodipine irregularly.',
    },
    {
      stage: 'physical_exam',
      info: 'Patient appears anxious, diaphoretic. Cardiovascular: S1 S2 present, no murmurs. Chest: Clear bilaterally. JVP not elevated. No pedal edema. Cold, clammy extremities.',
    },
    {
      stage: 'labs',
      info: 'ECG: ST elevation in leads II, III, aVF (inferior wall MI). Troponin-I: Elevated at 2.5 ng/mL. CPK-MB: Elevated. Blood sugar: 280 mg/dL. Lipid profile: Total cholesterol 240, LDL 160, HDL 35.',
    },
  ],
  diagnosis: 'Acute ST-elevation myocardial infarction (STEMI) - Inferior wall',
  learning_points: [
    'Time is muscle - Door to balloon time critical in STEMI',
    'Classic presentation: Crushing chest pain, radiation, diaphoresis',
    'ECG is diagnostic - ST elevation in contiguous leads',
    'Immediate dual antiplatelet therapy (Aspirin + Clopidogrel)',
    'Primary PCI is treatment of choice if available within 90 minutes',
  ],
  script: {
    questions: [
      "Can you describe your chest pain?",
      "What are the current vital signs?",
      "Let's do an ECG immediately",
      "Start oxygen and give aspirin 325mg stat",
      "We need to activate the cath lab - this is a STEMI",
    ],
    initialMessages: [
      {
        id: 'demo-init-1',
        agent_type: 'nurse',
        display_name: 'Nurse Priya',
        content: 'Doctor, urgent case! 55-year-old male with severe chest pain. BP is dropping - 90/60, pulse 110. Patient is sweating profusely. I\'ve started IV access and put him on monitor.',
        urgency_level: 'critical',
        timestamp: new Date(),
      },
      {
        id: 'demo-init-2',
        agent_type: 'patient',
        display_name: 'Patient',
        content: 'Doctor sahab... bahut dard ho raha hai... chest mein... jaise koi dabaa raha ho... haath tak jaa raha hai... (groaning in pain) Please kuch karo!',
        distress_level: 'critical',
        timestamp: new Date(),
      },
      {
        id: 'demo-init-3',
        agent_type: 'family',
        display_name: "Patient's Wife",
        content: 'Doctor please bachaa lo inko! Stairs chadhte waqt achanak gir gaye... bahut pasina aa raha tha... kabhi aisa nahi hua! Yeh BP aur sugar ki dawai lete hain par irregular. Please jaldi kuch karo!',
        timestamp: new Date(),
      },
      {
        id: 'demo-init-4',
        agent_type: 'senior_doctor',
        display_name: 'Dr. Sharma',
        content: 'This looks concerning. The presentation is classic - what\'s your immediate assessment? Think about the most life-threatening causes of chest pain. Time is critical here.',
        is_teaching: true,
        timestamp: new Date(),
      },
    ],
    responses: {
      "Can you describe your chest pain?": [
        {
          id: 'resp-1',
          agent_type: 'patient',
          display_name: 'Patient',
          content: 'Doctor... bahut tez dard... jaise pathhar rakha ho chest pe... 2 ghante se ho raha hai... left haath mein bhi jaa raha hai... saans lene mein bhi dikkat... (sweating profusely)',
          distress_level: 'critical',
          timestamp: new Date(),
        },
      ],
      "What are the current vital signs?": [
        {
          id: 'resp-2',
          agent_type: 'nurse',
          display_name: 'Nurse Priya',
          content: 'Doctor, vitals are worrying - BP 90/60 and dropping, pulse 110 irregular, RR 24, SpO2 94% on room air, patient is diaphoretic. ECG machine is ready.',
          urgency_level: 'critical',
          timestamp: new Date(),
        },
      ],
      "Let's do an ECG immediately": [
        {
          id: 'resp-3',
          agent_type: 'nurse',
          display_name: 'Nurse Priya',
          content: 'ECG done doctor - showing ST elevation in leads II, III, and aVF. This looks like an inferior wall MI!',
          urgency_level: 'critical',
          timestamp: new Date(),
        },
        {
          id: 'resp-4',
          agent_type: 'senior_doctor',
          display_name: 'Dr. Sharma',
          content: 'Excellent! You\'ve identified a STEMI. Now every minute counts. What\'s your immediate management? Remember - Time is muscle!',
          is_teaching: true,
          timestamp: new Date(),
        },
      ],
      "Start oxygen and give aspirin 325mg stat": [
        {
          id: 'resp-5',
          agent_type: 'nurse',
          display_name: 'Nurse Priya',
          content: 'Oxygen started at 4L/min via nasal cannula. Aspirin 325mg chewable given. Also giving Clopidogrel 300mg loading dose. Should I prepare for thrombolysis or are we going for primary PCI?',
          timestamp: new Date(),
        },
      ],
      "We need to activate the cath lab - this is a STEMI": [
        {
          id: 'resp-6',
          agent_type: 'senior_doctor',
          display_name: 'Dr. Sharma',
          content: 'Perfect management! You\'ve correctly identified and managed an acute STEMI. Door-to-balloon time is critical. The cath lab team is being activated. Remember the mnemonic MONA - Morphine, Oxygen, Nitrates, Aspirin. Excellent work!',
          is_teaching: true,
          timestamp: new Date(),
        },
        {
          id: 'resp-7',
          agent_type: 'patient',
          display_name: 'Patient',
          content: 'Doctor... thoda better lag raha hai oxygen ke baad... thank you... (still in pain but slightly relieved)',
          distress_level: 'high',
          timestamp: new Date(),
        },
      ],
    },
  },
};

// Case 2: Dengue Fever (Common tropical disease for demo)
const dengueCase: DemoCase = {
  id: 'demo-dengue-001',
  title: 'Dengue Fever with Warning Signs',
  description: 'Common tropical disease showing importance of monitoring and supportive care',
  specialty: 'Infectious Disease',
  difficulty: 'beginner',
  patient: {
    age: 28,
    gender: 'Female',
    location: 'Delhi',
  },
  chief_complaint: 'High fever with body aches for 4 days',
  initial_presentation: '28-year-old female teacher presents with high-grade fever for 4 days, severe body aches, headache behind eyes, and new-onset skin rash. No appetite, mild abdominal pain.',
  vital_signs: {
    bp: '100/70',
    hr: 95,
    rr: 18,
    temp: 39.2,
    spo2: 98,
  },
  stages: [
    {
      stage: 'history',
      info: 'Fever started 4 days ago, initially 103°F, now 102°F. Severe retro-orbital headache, myalgia, arthralgia (breakbone fever). Developed rash today - red, patchy. Mild abdominal pain, nausea, decreased appetite. No bleeding manifestations. Multiple mosquito bites last week. Neighbor also had dengue recently.',
    },
    {
      stage: 'physical_exam',
      info: 'Patient appears tired but alert. Positive tourniquet test. Petechial rash on arms and trunk. Mild right hypochondrial tenderness. No hepatosplenomegaly. No signs of plasma leakage.',
    },
    {
      stage: 'labs',
      info: 'CBC: Platelets 80,000 (falling trend), WBC 3,500, Hct 42% (baseline 38%). Dengue NS1 Antigen: Positive. Dengue IgM: Positive. LFT: Mild transaminitis (AST 120, ALT 100).',
    },
  ],
  diagnosis: 'Dengue fever with warning signs',
  learning_points: [
    'Dengue has three phases: Febrile, Critical (day 3-7), Recovery',
    'Warning signs: Abdominal pain, persistent vomiting, clinical fluid accumulation',
    'Monitor platelet count and hematocrit daily',
    'IV fluids crucial if warning signs present',
    'Avoid NSAIDs and IM injections due to bleeding risk',
  ],
  script: {
    questions: [
      "How long have you had this fever?",
      "Any bleeding from anywhere?",
      "What's the platelet count?",
      "Let's start IV fluids and monitor closely",
      "This looks like dengue - we need daily platelet monitoring",
    ],
    initialMessages: [
      {
        id: 'demo-init-d1',
        agent_type: 'nurse',
        display_name: 'Nurse Priya',
        content: 'Doctor, 28-year-old female with high fever for 4 days. She looks weak. Today morning she developed a rash all over. Platelet count from yesterday was 1.2 lakh, today it\'s 80,000.',
        urgency_level: 'urgent',
        timestamp: new Date(),
      },
      {
        id: 'demo-init-d2',
        agent_type: 'patient',
        display_name: 'Patient',
        content: 'Doctor, bahut weakness ho rahi hai... sar mein aur aankhon ke peeche bahut dard... pura badan dukh raha hai jaise haddiyan toot rahi hon... bukhar 4 din se hai...',
        distress_level: 'moderate',
        timestamp: new Date(),
      },
      {
        id: 'demo-init-d3',
        agent_type: 'family',
        display_name: "Patient's Mother",
        content: 'Doctor ji, kal se kuch bhi nahi khaya hai... bas paani pi rahi hai... aaj subah se yeh red red spots aa gaye hain... mohalle mein kaafi logon ko dengue hua hai. Please check kar lijiye!',
        timestamp: new Date(),
      },
      {
        id: 'demo-init-d4',
        agent_type: 'senior_doctor',
        display_name: 'Dr. Sharma',
        content: 'Classic presentation in dengue season. Note the timing - day 4 of illness. What phase of dengue is this? What warning signs should we monitor for?',
        is_teaching: true,
        timestamp: new Date(),
      },
    ],
    responses: {
      "How long have you had this fever?": [
        {
          id: 'resp-d1',
          agent_type: 'patient',
          display_name: 'Patient',
          content: 'Doctor, Monday se fever hai... pehle 103 tak jaata tha, ab thoda kam hai par body pain bahut zyada hai... aankhon ke peeche specially dard karta hai...',
          timestamp: new Date(),
        },
      ],
      "Any bleeding from anywhere?": [
        {
          id: 'resp-d2',
          agent_type: 'patient',
          display_name: 'Patient',
          content: 'Nahi doctor, bleeding toh nahi hai... par aaj brush karte time gums se thoda sa blood aaya tha... normally nahi hota...',
          timestamp: new Date(),
        },
        {
          id: 'resp-d2b',
          agent_type: 'family',
          display_name: "Patient's Mother",
          content: 'Doctor, kal nose se bhi ek baar thoda blood aaya tha, par humne socha garmi ki wajah se hoga...',
          timestamp: new Date(),
        },
      ],
      "What's the platelet count?": [
        {
          id: 'resp-d3',
          agent_type: 'nurse',
          display_name: 'Nurse Priya',
          content: 'Latest platelet count is 80,000 doctor. It was 1.2 lakh yesterday, and 1.5 lakh two days ago. Clear falling trend. Hematocrit is 42% (was 38% at baseline). Should we repeat in evening?',
          urgency_level: 'urgent',
          timestamp: new Date(),
        },
        {
          id: 'resp-d3b',
          agent_type: 'lab_tech',
          display_name: 'Lab Tech Ramesh',
          content: 'Doctor, Dengue NS1 positive hai. IgM bhi positive. LFT mein mild elevation hai - AST 120, ALT 100. Platelet ka repeat 6 ghante mein karenge?',
          timestamp: new Date(),
        },
      ],
      "Let's start IV fluids and monitor closely": [
        {
          id: 'resp-d4',
          agent_type: 'nurse',
          display_name: 'Nurse Priya',
          content: 'IV line secured, starting NS at 100ml/hr as ordered. Will monitor intake-output strictly. Vital signs every 4 hours. Should I give paracetamol for fever?',
          timestamp: new Date(),
        },
      ],
      "This looks like dengue - we need daily platelet monitoring": [
        {
          id: 'resp-d5',
          agent_type: 'senior_doctor',
          display_name: 'Dr. Sharma',
          content: 'Excellent! You\'ve identified dengue with warning signs - falling platelets and mild bleeding. This is the critical phase (days 3-7). Key is supportive care - IV fluids, monitoring for plasma leakage. No aspirin or NSAIDs! Well managed!',
          is_teaching: true,
          timestamp: new Date(),
        },
        {
          id: 'resp-d6',
          agent_type: 'family',
          display_name: "Patient's Mother",
          content: 'Thank you doctor... kitne din mein theek ho jayegi? Ghar le ja sakte hain ya admit karna padega?',
          timestamp: new Date(),
        },
      ],
    },
  },
};

export const DEMO_CASES = [miCase, dengueCase];

export const getDemoCase = (id: string): DemoCase | undefined => {
  return DEMO_CASES.find(c => c.id === id);
};