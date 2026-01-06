/**
 * Album Wizard Modal - Multi-step form for creating albums
 * Steps: 1. Album Information, 2. Pressing Details, 3. Add to Collection
 */

import { useState, useRef } from 'react';
import { Modal } from '@/components/UI';
import { AlbumWithPressingForm } from '@/components/Forms';
import './AlbumWizardModal.css';

interface AlbumWizardModalProps {
  initialArtistId?: string;
  initialArtistName?: string;
  initialArtistDiscogsId?: number | null;
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

type WizardStep = 1 | 2 | 3;

const STEP_TITLES = {
  1: 'Step 1: Album Information',
  2: 'Step 2: Pressing Details',
  3: 'Step 3: Add to Collection',
};

export function AlbumWizardModal({ initialArtistId, initialArtistName, initialArtistDiscogsId, isOpen, onClose, onSuccess }: AlbumWizardModalProps) {
  const [currentStep, setCurrentStep] = useState<WizardStep>(1);
  const [albumOnly, setAlbumOnly] = useState(false);
  const [albumAndPressingOnly, setAlbumAndPressingOnly] = useState(false);
  const formRef = useRef<{ submit: () => void }>(null);
  const contentRef = useRef<HTMLDivElement>(null);

  const handleNext = () => {
    if (currentStep < 3) {
      setCurrentStep((prev) => (prev + 1) as WizardStep);
      // Scroll to top of wizard content
      if (contentRef.current) {
        contentRef.current.scrollTop = 0;
      }
    }
  };

  const handleCreateAlbum = () => {
    // Trigger form submission for album-only creation
    if (formRef.current) {
      formRef.current.submit();
    }
  };

  const handleCreateAlbumAndPressing = () => {
    // Trigger form submission for album and pressing creation
    if (formRef.current) {
      formRef.current.submit();
    }
  };

  const handleAddToCollection = () => {
    // Trigger form submission for full creation (album + pressing + collection)
    if (formRef.current) {
      formRef.current.submit();
    }
  };

  const handleBack = () => {
    if (currentStep > 1) {
      setCurrentStep((prev) => (prev - 1) as WizardStep);
      // Scroll to top of wizard content
      if (contentRef.current) {
        contentRef.current.scrollTop = 0;
      }
    }
  };

  const handleCancel = () => {
    setCurrentStep(1);
    setAlbumOnly(false);
    setAlbumAndPressingOnly(false);
    onClose();
  };

  const handleSuccess = () => {
    setCurrentStep(1);
    setAlbumOnly(false);
    setAlbumAndPressingOnly(false);
    onSuccess();
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={handleCancel}
      title={STEP_TITLES[currentStep]}
      size="large"
    >
      <div className="album-wizard">
        {/* Step Indicator */}
        <div className="wizard-steps">
          {[1, 2, 3].map((step) => (
            <div
              key={step}
              className={`wizard-step ${currentStep === step ? 'active' : ''} ${
                currentStep > step ? 'completed' : ''
              }`}
            >
              <div className="wizard-step-number">{step}</div>
              <div className="wizard-step-label">
                {step === 1 && 'Album'}
                {step === 2 && 'Pressing'}
                {step === 3 && 'Collection'}
              </div>
            </div>
          ))}
        </div>

        {/* Form Content */}
        <div ref={contentRef} className="wizard-content">
          <AlbumWithPressingForm
            ref={formRef}
            initialArtistId={initialArtistId}
            initialArtistName={initialArtistName}
            initialArtistDiscogsId={initialArtistDiscogsId}
            onSuccess={handleSuccess}
            onCancel={handleCancel}
            wizardStep={currentStep}
            albumOnly={albumOnly}
            albumAndPressingOnly={albumAndPressingOnly}
          />
        </div>

        {/* Navigation Buttons */}
        <div className="wizard-navigation">
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            <button
              type="button"
              className="btn-secondary"
              onClick={handleCancel}
            >
              Cancel
            </button>
            {currentStep === 1 && (
              <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer', color: '#e0e0e0' }}>
                <input
                  type="checkbox"
                  checked={albumOnly}
                  onChange={(e) => setAlbumOnly(e.target.checked)}
                  style={{ width: '18px', height: '18px', cursor: 'pointer' }}
                />
                <span>Album Only</span>
              </label>
            )}
            {currentStep === 2 && (
              <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer', color: '#e0e0e0' }}>
                <input
                  type="checkbox"
                  checked={albumAndPressingOnly}
                  onChange={(e) => setAlbumAndPressingOnly(e.target.checked)}
                  style={{ width: '18px', height: '18px', cursor: 'pointer' }}
                />
                <span>Album and Pressing Only</span>
              </label>
            )}
          </div>
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            {currentStep > 1 && (
              <button
                type="button"
                className="btn-secondary"
                onClick={handleBack}
              >
                Back
              </button>
            )}
            {currentStep < 3 ? (
              <button
                type="button"
                className="btn-primary"
                onClick={
                  albumOnly && currentStep === 1
                    ? handleCreateAlbum
                    : albumAndPressingOnly && currentStep === 2
                    ? handleCreateAlbumAndPressing
                    : handleNext
                }
              >
                {albumOnly && currentStep === 1
                  ? 'Create Album'
                  : albumAndPressingOnly && currentStep === 2
                  ? 'Create Album and Pressing'
                  : 'Next'}
              </button>
            ) : (
              <button
                type="button"
                className="btn-primary"
                onClick={handleAddToCollection}
              >
                Add to My Collection
              </button>
            )}
          </div>
        </div>
      </div>
    </Modal>
  );
}
