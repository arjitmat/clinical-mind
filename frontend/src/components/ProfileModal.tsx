/**
 * ProfileModal - Collects student profile before starting feature
 */
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';

export type YearLevel = 'final_year' | 'internship' | 'residency' | 'practicing';
export type PracticeSetting = 'urban' | 'rural' | 'community';
export type Specialty = 'cardiology' | 'respiratory' | 'infectious' | 'neurology' | 'gastro' | 'emergency' | 'pediatrics' | 'obstetrics';

export interface StudentProfile {
  yearLevel: YearLevel;
  comfortableSpecialties: Specialty[];
  setting: PracticeSetting;
}

interface ProfileModalProps {
  isOpen: boolean;
  onClose: () => void;
  selectedFeature: string;
}

export const ProfileModal: React.FC<ProfileModalProps> = ({
  isOpen,
  onClose,
  selectedFeature,
}) => {
  const navigate = useNavigate();
  const [yearLevel, setYearLevel] = useState<YearLevel>('final_year');
  const [setting, setSetting] = useState<PracticeSetting>('urban');
  const [specialties, setSpecialties] = useState<Specialty[]>([]);

  if (!isOpen) return null;

  const handleSpecialtyToggle = (specialty: Specialty) => {
    if (specialties.includes(specialty)) {
      setSpecialties(specialties.filter(s => s !== specialty));
    } else {
      setSpecialties([...specialties, specialty]);
    }
  };

  const handleContinue = () => {
    const profile: StudentProfile = {
      yearLevel,
      comfortableSpecialties: specialties,
      setting,
    };

    // Store profile in localStorage
    localStorage.setItem('studentProfile', JSON.stringify(profile));

    // Navigate to feature (will trigger case selection)
    navigate(`/${selectedFeature}?new=true`);
  };

  const specialtyOptions: { id: Specialty; label: string }[] = [
    { id: 'cardiology', label: 'Cardiology' },
    { id: 'respiratory', label: 'Respiratory' },
    { id: 'infectious', label: 'Infectious Disease' },
    { id: 'neurology', label: 'Neurology' },
    { id: 'gastro', label: 'Gastroenterology' },
    { id: 'emergency', label: 'Emergency Medicine' },
    { id: 'pediatrics', label: 'Pediatrics' },
    { id: 'obstetrics', label: 'Obstetrics' },
  ];

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-6 animate-fade-in-up">
      <div className="bg-white rounded-2xl p-8 max-w-lg w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="mb-6">
          <h2 className="text-2xl font-bold text-text-primary mb-2">
            Tell us about yourself
          </h2>
          <p className="text-text-secondary">
            This helps us choose the right case for you
          </p>
        </div>

        {/* Year Level */}
        <div className="mb-6">
          <label className="block text-sm font-semibold text-text-primary mb-3">
            What's your level?
          </label>
          <div className="space-y-2">
            {[
              { id: 'final_year' as YearLevel, label: 'Final Year MBBS' },
              { id: 'internship' as YearLevel, label: 'Internship' },
              { id: 'residency' as YearLevel, label: 'Residency/PG' },
              { id: 'practicing' as YearLevel, label: 'Practicing Doctor' },
            ].map((option) => (
              <label
                key={option.id}
                className="flex items-center gap-3 p-3 rounded-xl border border-warm-gray-200 hover:bg-warm-gray-50 cursor-pointer transition-all"
              >
                <input
                  type="radio"
                  name="yearLevel"
                  value={option.id}
                  checked={yearLevel === option.id}
                  onChange={(e) => setYearLevel(e.target.value as YearLevel)}
                  className="w-4 h-4 text-forest-green"
                />
                <span className="text-base text-text-primary">{option.label}</span>
              </label>
            ))}
          </div>
        </div>

        {/* Specialties */}
        <div className="mb-6">
          <label className="block text-sm font-semibold text-text-primary mb-3">
            Which specialties are you comfortable with?
            <span className="text-text-tertiary font-normal ml-2">(Select all that apply)</span>
          </label>
          <div className="grid grid-cols-2 gap-2">
            {specialtyOptions.map((option) => (
              <label
                key={option.id}
                className="flex items-center gap-2 p-3 rounded-xl border border-warm-gray-200 hover:bg-warm-gray-50 cursor-pointer transition-all"
              >
                <input
                  type="checkbox"
                  checked={specialties.includes(option.id)}
                  onChange={() => handleSpecialtyToggle(option.id)}
                  className="w-4 h-4 text-forest-green rounded"
                />
                <span className="text-sm text-text-primary">{option.label}</span>
              </label>
            ))}
          </div>
        </div>

        {/* Setting */}
        <div className="mb-8">
          <label className="block text-sm font-semibold text-text-primary mb-3">
            Where do you practice/study?
          </label>
          <div className="space-y-2">
            {[
              { id: 'urban' as PracticeSetting, label: 'Urban Medical College/Hospital' },
              { id: 'rural' as PracticeSetting, label: 'Rural Primary Health Center' },
              { id: 'community' as PracticeSetting, label: 'Community Health Center' },
            ].map((option) => (
              <label
                key={option.id}
                className="flex items-center gap-3 p-3 rounded-xl border border-warm-gray-200 hover:bg-warm-gray-50 cursor-pointer transition-all"
              >
                <input
                  type="radio"
                  name="setting"
                  value={option.id}
                  checked={setting === option.id}
                  onChange={(e) => setSetting(e.target.value as PracticeSetting)}
                  className="w-4 h-4 text-forest-green"
                />
                <span className="text-base text-text-primary">{option.label}</span>
              </label>
            ))}
          </div>
        </div>

        {/* Actions */}
        <div className="flex gap-3">
          <button
            onClick={onClose}
            className="flex-1 bg-warm-gray-100 hover:bg-warm-gray-200 text-text-primary font-semibold py-3 px-6 rounded-xl transition-all duration-300"
          >
            Cancel
          </button>
          <button
            onClick={handleContinue}
            className="flex-1 bg-forest-green hover:bg-forest-green-dark text-cream-white font-semibold py-3 px-6 rounded-xl transition-all duration-300"
          >
            Continue to Feature →
          </button>
        </div>
      </div>
    </div>
  );
};
