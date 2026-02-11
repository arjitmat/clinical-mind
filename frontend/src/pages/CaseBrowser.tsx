import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button, Card, Badge } from '../components/ui';
import { fetchSpecialties, generateCase, type SpecialtyDTO, type GeneratedCase } from '../hooks/useApi';

const difficulties = [
  { id: 'all', name: 'All Levels' },
  { id: 'beginner', name: 'Beginner' },
  { id: 'intermediate', name: 'Intermediate' },
  { id: 'advanced', name: 'Advanced' },
];

const difficultyColors: Record<string, 'success' | 'warning' | 'error'> = {
  beginner: 'success',
  intermediate: 'warning',
  advanced: 'error',
};

export const CaseBrowser: React.FC = () => {
  const navigate = useNavigate();
  const [specialties, setSpecialties] = useState<SpecialtyDTO[]>([]);
  const [selectedSpecialty, setSelectedSpecialty] = useState('all');
  const [selectedDifficulty, setSelectedDifficulty] = useState('all');
  const [generatedCases, setGeneratedCases] = useState<GeneratedCase[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchSpecialties()
      .then((data) => setSpecialties(data.specialties))
      .catch(() => setError('Failed to load specialties. Is the backend running?'));
  }, []);

  // Generate preview cases on mount
  useEffect(() => {
    const previewSpecs = ['cardiology', 'infectious', 'neurology', 'respiratory', 'gastro', 'emergency'];
    const previewDiffs = ['intermediate', 'beginner', 'advanced', 'beginner', 'intermediate', 'advanced'];
    Promise.allSettled(
      previewSpecs.map((s, i) => generateCase(s, previewDiffs[i]))
    ).then((results) => {
      const cases = results
        .filter((r): r is PromiseFulfilledResult<GeneratedCase> => r.status === 'fulfilled')
        .map((r) => r.value);
      setGeneratedCases(cases);
    });
  }, []);

  const handleGenerateCase = async () => {
    setLoading(true);
    setError('');
    try {
      const specialty = selectedSpecialty === 'all' ? 'cardiology' : selectedSpecialty;
      const difficulty = selectedDifficulty === 'all' ? 'intermediate' : selectedDifficulty;
      const newCase = await generateCase(specialty, difficulty);
      navigate(`/case/${newCase.id}`);
    } catch (e: any) {
      setError(e.message || 'Failed to generate case');
    } finally {
      setLoading(false);
    }
  };

  const filteredCases = generatedCases.filter((c) => {
    const matchSpecialty = selectedSpecialty === 'all' || c.specialty === selectedSpecialty;
    const matchDifficulty = selectedDifficulty === 'all' || c.difficulty === selectedDifficulty;
    return matchSpecialty && matchDifficulty;
  });

  const specialtyFilters = [{ id: 'all', name: 'All Specialties' }, ...specialties.map((s) => ({ id: s.id, name: s.name }))];

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

      {error && (
        <div className="bg-terracotta/10 text-terracotta rounded-xl p-4 mb-6 text-sm">{error}</div>
      )}

      {/* Filters */}
      <div className="flex flex-col md:flex-row gap-4 mb-8">
        <div className="flex flex-wrap gap-2">
          {specialtyFilters.slice(0, 7).map((s) => (
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
          <Button onClick={handleGenerateCase} disabled={loading}>
            {loading ? 'Generating...' : 'Generate Case'}
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
              <Badge variant={difficultyColors[caseItem.difficulty] || 'warning'}>
                {caseItem.difficulty.charAt(0).toUpperCase() + caseItem.difficulty.slice(1)}
              </Badge>
              <span className="text-sm text-text-tertiary">{caseItem.patient.location}</span>
            </div>
            <h3 className="text-lg font-semibold text-text-primary mb-2">{caseItem.chief_complaint}</h3>
            <p className="text-base text-text-secondary mb-4 leading-relaxed">
              {caseItem.initial_presentation.slice(0, 180)}...
            </p>
            <div className="flex flex-wrap gap-2">
              <Badge variant="default" size="sm">{caseItem.specialty}</Badge>
              {caseItem.differentials?.slice(0, 2).map((d) => (
                <Badge key={d} variant="default" size="sm">{d}</Badge>
              ))}
            </div>
          </Card>
        ))}
      </div>

      {filteredCases.length === 0 && generatedCases.length > 0 && (
        <div className="text-center py-16">
          <p className="text-lg text-text-tertiary mb-4">No cases match your filters</p>
          <Button variant="secondary" onClick={() => { setSelectedSpecialty('all'); setSelectedDifficulty('all'); }}>
            Clear Filters
          </Button>
        </div>
      )}

      {generatedCases.length === 0 && !error && (
        <div className="text-center py-16">
          <div className="animate-pulse text-lg text-text-tertiary">Loading cases from backend...</div>
        </div>
      )}
    </div>
  );
};
