import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button, Card, Badge } from '../components/ui';

const specialties = [
  { id: 'all', name: 'All Specialties' },
  { id: 'cardiology', name: 'Cardiology' },
  { id: 'respiratory', name: 'Respiratory' },
  { id: 'infectious', name: 'Infectious Disease' },
  { id: 'neurology', name: 'Neurology' },
  { id: 'gastro', name: 'Gastroenterology' },
  { id: 'emergency', name: 'Emergency Medicine' },
];

const difficulties = [
  { id: 'all', name: 'All Levels' },
  { id: 'beginner', name: 'Beginner' },
  { id: 'intermediate', name: 'Intermediate' },
  { id: 'advanced', name: 'Advanced' },
];

const sampleCases = [
  {
    id: 'case-1',
    title: 'Chest Pain in a Young Male',
    specialty: 'cardiology',
    difficulty: 'intermediate' as const,
    setting: 'Urban Emergency Department, Mumbai',
    snippet: 'A 28-year-old male presents to the ED with acute onset chest pain radiating to the left arm. He appears anxious and diaphoretic...',
    tags: ['ACS', 'Differential Diagnosis', 'ECG Interpretation'],
  },
  {
    id: 'case-2',
    title: 'Fever with Thrombocytopenia',
    specialty: 'infectious',
    difficulty: 'beginner' as const,
    setting: 'District Hospital, Kerala (Monsoon Season)',
    snippet: 'A 35-year-old female presents with 5 days of high-grade fever, myalgia, and a positive tourniquet test. Platelet count: 45,000...',
    tags: ['Dengue', 'Tropical Medicine', 'Fluid Management'],
  },
  {
    id: 'case-3',
    title: 'Progressive Weakness with Respiratory Distress',
    specialty: 'neurology',
    difficulty: 'advanced' as const,
    setting: 'Tertiary Care Hospital, Delhi',
    snippet: 'A 42-year-old teacher presents with ascending weakness over 3 days, now with difficulty breathing. Deep tendon reflexes are absent...',
    tags: ['GBS', 'Neuromuscular Emergency', 'Ventilation'],
  },
  {
    id: 'case-4',
    title: 'Chronic Cough in a Rural Setting',
    specialty: 'respiratory',
    difficulty: 'beginner' as const,
    setting: 'Primary Health Centre, Rajasthan',
    snippet: 'A 50-year-old farmer presents with productive cough for 3 weeks, evening rise of temperature, and significant weight loss...',
    tags: ['TB', 'RNTCP', 'Sputum Analysis'],
  },
  {
    id: 'case-5',
    title: 'Acute Abdomen with Hematemesis',
    specialty: 'gastro',
    difficulty: 'intermediate' as const,
    setting: 'Community Hospital, Tamil Nadu',
    snippet: 'A 45-year-old male with known alcohol use presents with severe epigastric pain and coffee-ground vomitus. He is tachycardic...',
    tags: ['Upper GI Bleed', 'Portal Hypertension', 'Resuscitation'],
  },
  {
    id: 'case-6',
    title: 'Pediatric Seizure with Altered Sensorium',
    specialty: 'emergency',
    difficulty: 'advanced' as const,
    setting: 'Emergency Department, Kolkata',
    snippet: 'A 4-year-old child is brought in with generalized tonic-clonic seizures lasting 10 minutes. Temperature is 39.8°C. Parents report recent travel...',
    tags: ['Status Epilepticus', 'Cerebral Malaria', 'Pediatric Emergency'],
  },
];

const difficultyColors: Record<string, 'success' | 'warning' | 'error'> = {
  beginner: 'success',
  intermediate: 'warning',
  advanced: 'error',
};

export const CaseBrowser: React.FC = () => {
  const navigate = useNavigate();
  const [selectedSpecialty, setSelectedSpecialty] = useState('all');
  const [selectedDifficulty, setSelectedDifficulty] = useState('all');

  const filteredCases = sampleCases.filter((c) => {
    const matchSpecialty = selectedSpecialty === 'all' || c.specialty === selectedSpecialty;
    const matchDifficulty = selectedDifficulty === 'all' || c.difficulty === selectedDifficulty;
    return matchSpecialty && matchDifficulty;
  });

  return (
    <div className="max-w-7xl mx-auto px-6 py-10">
      {/* Page Header */}
      <div className="mb-10">
        <h1 className="text-2xl md:text-[2.25rem] font-bold text-text-primary mb-3">
          Clinical Cases
        </h1>
        <p className="text-lg text-text-secondary">
          Choose a case to begin. Each case is dynamically generated from Indian medical literature.
        </p>
      </div>

      {/* Filters */}
      <div className="flex flex-col md:flex-row gap-4 mb-8">
        <div className="flex flex-wrap gap-2">
          {specialties.map((s) => (
            <button
              key={s.id}
              onClick={() => setSelectedSpecialty(s.id)}
              className={`px-4 py-2 rounded-xl text-sm font-medium transition-all duration-300 cursor-pointer border-none ${
                selectedSpecialty === s.id
                  ? 'bg-forest-green text-cream-white'
                  : 'bg-warm-gray-50 text-text-secondary hover:bg-warm-gray-100'
              }`}
            >
              {s.name}
            </button>
          ))}
        </div>
        <div className="flex flex-wrap gap-2">
          {difficulties.map((d) => (
            <button
              key={d.id}
              onClick={() => setSelectedDifficulty(d.id)}
              className={`px-4 py-2 rounded-xl text-sm font-medium transition-all duration-300 cursor-pointer border-none ${
                selectedDifficulty === d.id
                  ? 'bg-forest-green text-cream-white'
                  : 'bg-warm-gray-50 text-text-secondary hover:bg-warm-gray-100'
              }`}
            >
              {d.name}
            </button>
          ))}
        </div>
      </div>

      {/* Generate New Case */}
      <Card padding="lg" className="mb-8 border-dashed border-2 border-forest-green/30 bg-forest-green/[0.02]">
        <div className="flex flex-col md:flex-row items-center justify-between gap-4">
          <div>
            <h3 className="text-lg font-semibold text-text-primary mb-1">Generate a New Case</h3>
            <p className="text-base text-text-secondary">
              Our RAG system creates unique cases from Indian medical journals. No two cases are alike.
            </p>
          </div>
          <Button onClick={() => navigate('/case/new')}>
            Generate Case
          </Button>
        </div>
      </Card>

      {/* Case Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {filteredCases.map((caseItem) => (
          <Card
            key={caseItem.id}
            hover
            padding="lg"
            onClick={() => navigate(`/case/${caseItem.id}`)}
          >
            <div className="flex items-start justify-between mb-3">
              <Badge variant={difficultyColors[caseItem.difficulty]}>
                {caseItem.difficulty.charAt(0).toUpperCase() + caseItem.difficulty.slice(1)}
              </Badge>
              <span className="text-sm text-text-tertiary">{caseItem.setting}</span>
            </div>
            <h3 className="text-lg font-semibold text-text-primary mb-2">{caseItem.title}</h3>
            <p className="text-base text-text-secondary mb-4 leading-relaxed">{caseItem.snippet}</p>
            <div className="flex flex-wrap gap-2">
              {caseItem.tags.map((tag) => (
                <Badge key={tag} variant="default" size="sm">{tag}</Badge>
              ))}
            </div>
          </Card>
        ))}
      </div>

      {filteredCases.length === 0 && (
        <div className="text-center py-16">
          <p className="text-lg text-text-tertiary mb-4">No cases match your filters</p>
          <Button variant="secondary" onClick={() => { setSelectedSpecialty('all'); setSelectedDifficulty('all'); }}>
            Clear Filters
          </Button>
        </div>
      )}
    </div>
  );
};
