/**
 * Pressing Wizard Modal - Multi-step form for creating pressings
 * Steps: 1. Pressing Details, 2. Add to Collection
 */

import { useState, useRef } from 'react';
import { Modal } from '@/components/UI';
import { AlbumWithPressingForm } from '@/components/Forms';
import './AlbumWizardModal.css';

interface PressingWizardModalProps {
  albumId: string;
  albumTitle: string;
  artistName: string;
  discogsId?: number | null;
  artistDiscogsId?: number | null;
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

type WizardStep = 1 | 2;

const STEP_TITLES = {
  1: 'Step 1: Pressing Details',
  2: 'Step 2: Add to Collection',
};

export function PressingWizardModal({ albumId, albumTitle, artistName, discogsId, artistDiscogsId, isOpen, onClose, onSuccess }: PressingWizardModalProps) {
  const [currentStep, setCurrentStep] = useState<WizardStep>(1);
  const [pressingOnly, setPressingOnly] = useState(false);
  const formRef = useRef<{ submit: () => void }>(null);
  const contentRef = useRef<HTMLDivElement>(null);

  const handleNext = () => {
    if (currentStep < 2) {
      setCurrentStep((prev) => (prev + 1) as WizardStep);
      // Scroll to top of wizard content
      if (contentRef.current) {
        contentRef.current.scrollTop = 0;
      }
    }
  };

  const handleCreatePressing = () => {
    // Trigger form submission for pressing-only creation
    if (formRef.current) {
      formRef.current.submit();
    }
  };

  const handleAddToCollection = () => {
    // Trigger form submission for full creation (pressing + collection)
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
    setPressingOnly(false);
    onClose();
  };

  const handleSuccess = () => {
    setCurrentStep(1);
    setPressingOnly(false);
    onSuccess();
  };

  // Map wizard step to form wizard step
  // Pressing Wizard Step 1 -> Form Wizard Step 2 (Pressing Details)
  // Pressing Wizard Step 2 -> Form Wizard Step 3 (Add to Collection)
  const formWizardStep = (currentStep + 1) as 2 | 3;

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
          {[1, 2].map((step) => (
            <div
              key={step}
              className={`wizard-step ${currentStep === step ? 'active' : ''} ${
                currentStep > step ? 'completed' : ''
              }`}
            >
              <div className="wizard-step-number">{step}</div>
              <div className="wizard-step-label">
                {step === 1 && 'Pressing'}
                {step === 2 && 'Collection'}
              </div>
            </div>
          ))}
        </div>

        {/* Form Content */}
        <div ref={contentRef} className="wizard-content">
          <AlbumWithPressingForm
            ref={formRef}
            initialAlbumId={albumId}
            initialAlbumTitle={albumTitle}
            initialArtistName={artistName}
            initialAlbumDiscogsId={discogsId}
            initialArtistDiscogsId={artistDiscogsId}
            onSuccess={handleSuccess}
            onCancel={handleCancel}
            wizardStep={formWizardStep}
            albumOnly={false}
            albumAndPressingOnly={pressingOnly}
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
                  checked={pressingOnly}
                  onChange={(e) => setPressingOnly(e.target.checked)}
                  style={{ width: '18px', height: '18px', cursor: 'pointer' }}
                />
                <span>Pressing Only</span>
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
            {currentStep < 2 ? (
              <button
                type="button"
                className="btn-primary"
                onClick={pressingOnly && currentStep === 1 ? handleCreatePressing : handleNext}
              >
                {pressingOnly && currentStep === 1 ? 'Create Pressing' : 'Next'}
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
