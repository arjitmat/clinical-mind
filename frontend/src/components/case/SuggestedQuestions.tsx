import React from 'react';

interface SuggestedQuestionsProps {
  activeAction: string;
  messageCount: number;
  hasVitals: boolean;
  hasHistory: boolean;
  hasExamination: boolean;
  hasInvestigations: boolean;
  onSelectQuestion: (question: string) => void;
  disabled?: boolean;
}

// Context-aware question suggestions based on clinical reasoning stages
const getContextualSuggestions = (
  action: string,
  messageCount: number,
  hasVitals: boolean,
  hasHistory: boolean,
  hasExamination: boolean,
  hasInvestigations: boolean
): string[] => {
  // Initial stage - gathering basic info
  if (messageCount < 3) {
    if (action === 'talk_to_patient') {
      return [
        "Can you tell me more about when this started?",
        "What makes the symptoms better or worse?",
        "Have you taken any medications for this?",
        "Any similar episodes in the past?",
      ];
    } else if (action === 'talk_to_family') {
      return [
        "What home remedies have you tried?",
        "Has anyone else in the family been sick?",
        "What medications does the patient regularly take?",
        "When did you first notice something was wrong?",
      ];
    } else if (action === 'ask_nurse') {
      return [
        "What are the current vital signs?",
        "Has the patient been eating and drinking?",
        "Any changes in the last hour?",
        "What was the initial presentation?",
      ];
    }
  }

  // History gathering stage
  if (!hasHistory || messageCount < 6) {
    if (action === 'talk_to_patient') {
      return [
        "Do you have any chronic medical conditions?",
        "Any allergies to medications?",
        "Do you smoke or drink alcohol?",
        "What's your occupation?",
      ];
    } else if (action === 'consult_senior') {
      return [
        "What should I focus on in the history?",
        "What red flags should I look for?",
        "What's your differential diagnosis?",
        "Should I order any urgent investigations?",
      ];
    }
  }

  // Examination stage
  if (!hasExamination && messageCount >= 6) {
    if (action === 'examine_patient') {
      return [
        "Examine cardiovascular system",
        "Examine respiratory system",
        "Examine abdomen",
        "Check for lymphadenopathy",
      ];
    } else if (action === 'ask_nurse') {
      return [
        "Can you help me examine the patient?",
        "Any notable physical findings you've observed?",
        "Is the patient stable for examination?",
        "Any skin changes or rashes?",
      ];
    }
  }

  // Investigation stage
  if (!hasInvestigations && messageCount >= 10) {
    if (action === 'order_investigation') {
      return [
        "CBC with differential",
        "Basic metabolic panel",
        "Chest X-ray",
        "ECG",
      ];
    } else if (action === 'ask_lab') {
      return [
        "What's the status of pending investigations?",
        "Can we expedite the blood work?",
        "Any critical values to report?",
        "How long for the imaging results?",
      ];
    }
  }

  // Treatment discussion stage
  if (hasInvestigations && messageCount >= 15) {
    if (action === 'order_treatment') {
      return [
        "Start IV fluids - NS 1L over 8 hours",
        "Oxygen via nasal cannula 2L/min",
        "Paracetamol 500mg PO for fever",
        "Start empirical antibiotics",
      ];
    } else if (action === 'team_huddle') {
      return [
        "Let's review the case so far",
        "What's our working diagnosis?",
        "Should we start empirical treatment?",
        "Do we need specialist consultation?",
      ];
    }
  }

  // Advanced reasoning stage
  if (messageCount >= 20) {
    if (action === 'consult_senior') {
      return [
        "I think the diagnosis is... Am I on the right track?",
        "Should we consider rare differentials?",
        "What would you do next in this case?",
        "Can you explain the pathophysiology?",
      ];
    }
  }

  // Default suggestions based on action
  const defaultSuggestions: Record<string, string[]> = {
    talk_to_patient: [
      "How are you feeling right now?",
      "Rate your pain from 1-10",
      "Any new symptoms?",
      "Are you comfortable?",
    ],
    talk_to_family: [
      "How long has this been going on?",
      "Any family history of similar issues?",
      "What are you most worried about?",
      "Has the patient's behavior changed?",
    ],
    ask_nurse: [
      "What are the latest vitals?",
      "Any concerning trends?",
      "Has the patient been compliant?",
      "Any nursing concerns?",
    ],
    ask_lab: [
      "When will the results be ready?",
      "Any preliminary findings?",
      "Can we rush these tests?",
      "What samples do you need?",
    ],
    consult_senior: [
      "What do you think about this case?",
      "Am I missing something important?",
      "Should I be worried?",
      "What's the next step?",
    ],
    examine_patient: [
      "General physical examination",
      "Focused system examination",
      "Check vital signs again",
      "Neurological examination",
    ],
    order_investigation: [
      "Complete blood count",
      "Blood glucose",
      "Urine routine",
      "Liver function tests",
    ],
    order_treatment: [
      "IV fluids",
      "Pain management",
      "Antipyretics",
      "Monitor vitals hourly",
    ],
    team_huddle: [
      "Let's discuss the differential diagnosis",
      "What are we missing?",
      "Review all findings so far",
      "Plan for the next 24 hours",
    ],
  };

  return defaultSuggestions[action] || defaultSuggestions.talk_to_patient;
};

export const SuggestedQuestions: React.FC<SuggestedQuestionsProps> = ({
  activeAction,
  messageCount,
  hasVitals,
  hasHistory,
  hasExamination,
  hasInvestigations,
  onSelectQuestion,
  disabled = false,
}) => {
  const suggestions = getContextualSuggestions(
    activeAction,
    messageCount,
    hasVitals,
    hasHistory,
    hasExamination,
    hasInvestigations
  );

  return (
    <div className="px-2 py-2 border-t border-warm-gray-100">
      <div className="flex items-center gap-2 mb-1.5">
        <span className="text-[10px] font-medium text-text-tertiary uppercase tracking-wide">
          Suggested Questions
        </span>
        <div className="h-[1px] flex-1 bg-warm-gray-100"></div>
      </div>
      <div className="flex flex-wrap gap-1.5">
        {suggestions.map((question, index) => (
          <button
            key={index}
            onClick={() => onSelectQuestion(question)}
            disabled={disabled}
            className="text-xs px-2.5 py-1.5 rounded-lg bg-warm-gray-50 text-text-secondary hover:bg-warm-gray-100 hover:text-text-primary transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {question}
          </button>
        ))}
      </div>
    </div>
  );
};