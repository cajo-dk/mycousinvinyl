/**
 * Modal for adding a new pressing to an album with optional collection addition.
 */

import { Modal } from '../UI/Modal';
import { PressingForm } from '../Forms/PressingForm';

interface AddPressingModalProps {
  albumId: string;
  albumTitle: string;
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

export function AddPressingModal({ albumId, albumTitle, isOpen, onClose, onSuccess }: AddPressingModalProps) {
  const handleSuccess = () => {
    onSuccess();
    onClose();
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Add New Pressing"
      size="large"
    >
      <PressingForm
        albumId={albumId}
        albumTitle={albumTitle}
        showAddToCollection={true}
        onSuccess={handleSuccess}
        onCancel={onClose}
      />
    </Modal>
  );
}
