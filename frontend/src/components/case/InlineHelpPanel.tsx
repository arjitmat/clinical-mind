import React, { useState } from 'react';
import { Card } from '../ui';

interface HelpSection {
  title: string;
  content: string;
  icon: string;
}

const helpSections: HelpSection[] = [
  {
    title: 'Getting Started',
    icon: '🚀',
    content: `Think of yourself as a junior doctor in an Indian government hospital. You're managing a real patient with the help of the hospital team. Click any tab above the message box to choose who to talk to, then type your question and press Enter.`
  },
  {
    title: 'Who Can Help You',
    icon: '👥',
    content: `• **Patient**: The person you're treating. Speaks in simple Hindi/English. May be anxious or in pain.
• **Family**: Relative with the patient. Very emotional, speaks Hinglish, knows patient's habits and history.
• **Nurse Priya**: Your eyes and ears. She monitors vitals, notices changes, administers treatments.
• **Lab Tech Ramesh**: Handles all tests. Ask him about sample collection and when results will be ready.
• **Dr. Sharma**: Senior doctor who guides you with questions, not answers. Helps you think critically.`
  },
  {
    title: 'What You Can Do',
    icon: '⚕️',
    content: `• **Talk**: Click a person's tab, type your question, press Enter
• **Examine**: Click "Examine" tab to check specific body systems
• **Order Tests**: Click "Investigate" to order blood tests, X-rays, ECG, etc.
• **Give Treatment**: Click "Treat" to start medications or procedures
• **Team Discussion**: Click "Huddle" for everyone to discuss together`
  },
  {
    title: 'Reading the Vitals',
    icon: '❤️',
    content: `The vitals panel shows live patient data that updates every 5 seconds - just like a real monitor!
• Green numbers = normal
• Yellow/amber = concerning, needs attention
• Red = critical, act fast!
• Arrows (↑↓) show if values are trending up or down`
  },
  {
    title: 'Waiting for Tests',
    icon: '⏰',
    content: `Just like real hospitals, tests take time:
• CBC: ~20 minutes
• X-ray: ~30 minutes
• CT scan: ~45 minutes
Click "Wait for Results" to advance time by 30 minutes if you're waiting for tests.`
  },
  {
    title: 'Success Tips',
    icon: '💡',
    content: `• Start by talking to the patient about their symptoms
• Ask the family for background - they know things the patient won't tell
• Check with Nurse Priya about vitals trends and observations
• When stuck, consult Dr. Sharma - he'll guide your thinking
• Order relevant tests early - they take time
• Don't forget to examine the patient!`
  }
];

export const InlineHelpPanel: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [activeSection, setActiveSection] = useState(0);

  return (
    <>
      {/* Help Toggle Button - Fixed position */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={`fixed bottom-8 right-8 z-50 w-12 h-12 bg-forest-green hover:bg-forest-green-dark text-cream-white rounded-full shadow-lg transition-all duration-300 flex items-center justify-center ${
          isOpen ? 'rotate-45' : ''
        }`}
        aria-label="Toggle help panel"
      >
        <span className="text-xl">{isOpen ? '✕' : '?'}</span>
      </button>

      {/* Help Panel - Slides in from right */}
      <div className={`fixed top-0 right-0 h-full w-80 bg-white shadow-xl transform transition-transform duration-300 z-40 ${
        isOpen ? 'translate-x-0' : 'translate-x-full'
      }`}>
        <div className="h-full flex flex-col">
          {/* Header */}
          <div className="p-4 bg-forest-green text-cream-white">
            <h3 className="text-lg font-bold">Quick Help</h3>
            <p className="text-xs opacity-90 mt-1">Interactive guide for multi-agent simulation</p>
          </div>

          {/* Section Tabs */}
          <div className="flex flex-wrap gap-1 p-2 bg-warm-gray-50 border-b border-warm-gray-200">
            {helpSections.map((section, index) => (
              <button
                key={index}
                onClick={() => setActiveSection(index)}
                className={`text-xs px-2 py-1 rounded transition-colors ${
                  activeSection === index
                    ? 'bg-forest-green text-cream-white'
                    : 'bg-white text-text-secondary hover:bg-warm-gray-100'
                }`}
                title={section.title}
              >
                <span className="mr-1">{section.icon}</span>
                <span className="hidden sm:inline">{section.title.split(' ')[0]}</span>
              </button>
            ))}
          </div>

          {/* Content */}
          <div className="flex-1 overflow-y-auto p-4">
            <div className="space-y-4">
              <div className="animate-fade-in">
                <h4 className="text-sm font-semibold text-text-primary mb-2 flex items-center gap-2">
                  <span className="text-lg">{helpSections[activeSection].icon}</span>
                  {helpSections[activeSection].title}
                </h4>
                <div className="text-xs text-text-secondary leading-relaxed whitespace-pre-line">
                  {helpSections[activeSection].content.split('•').map((line, i) => {
                    if (i === 0) return <p key={i}>{line}</p>;
                    const [title, ...rest] = line.split(':');
                    return (
                      <div key={i} className="mb-2">
                        <span className="font-medium text-text-primary">• {title}:</span>
                        {rest.join(':')}
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Context-sensitive tips */}
              <div className="mt-4 p-3 bg-soft-blue/10 rounded-lg border border-soft-blue/20">
                <h5 className="text-xs font-semibold text-soft-blue mb-1">Quick Start</h5>
                <p className="text-xs text-text-secondary">
                  You're a junior doctor managing this patient. Start by clicking "Patient" tab above and ask "How are you feeling?" to begin your assessment.
                </p>
              </div>
            </div>
          </div>

          {/* Footer */}
          <div className="p-3 border-t border-warm-gray-200 bg-warm-gray-50">
            <p className="text-xs text-text-tertiary text-center">
              Press <kbd className="px-1.5 py-0.5 bg-white rounded text-xs">?</kbd> to toggle help
            </p>
          </div>
        </div>
      </div>

      {/* Overlay when help is open */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/20 z-30"
          onClick={() => setIsOpen(false)}
        />
      )}
    </>
  );
};

export default InlineHelpPanel;