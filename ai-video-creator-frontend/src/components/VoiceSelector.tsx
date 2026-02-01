import { useState } from 'react';
import { useVoices, useAssignVoice, useCreateVoice } from '../api';
import type { Voice } from '../types';

interface VoiceSelectorProps {
  projectId: string;
  currentVoiceId: string | null;
  onVoiceSelected?: (voiceId: string) => void;
}

export function VoiceSelector({
  projectId,
  currentVoiceId,
  onVoiceSelected,
}: VoiceSelectorProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [showAddForm, setShowAddForm] = useState(false);
  const [newVoiceId, setNewVoiceId] = useState('');
  const [newVoiceName, setNewVoiceName] = useState('');

  const { data: voicesData, isLoading: voicesLoading } = useVoices();
  const assignVoice = useAssignVoice();
  const createVoice = useCreateVoice();

  const voices = voicesData?.voices || [];

  const handleSelectVoice = async (voice: Voice) => {
    await assignVoice.mutateAsync({
      projectId,
      voiceId: voice.voiceId,
    });
    onVoiceSelected?.(voice.voiceId);
    setIsOpen(false);
  };

  const handleAddExistingVoice = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newVoiceId.trim() || !newVoiceName.trim()) return;

    try {
      // First create the voice record
      await createVoice.mutateAsync({
        voiceId: newVoiceId.trim(),
        name: newVoiceName.trim(),
      });

      // Then assign it to the project
      await assignVoice.mutateAsync({
        projectId,
        voiceId: newVoiceId.trim(),
      });

      onVoiceSelected?.(newVoiceId.trim());
      setNewVoiceId('');
      setNewVoiceName('');
      setShowAddForm(false);
      setIsOpen(false);
    } catch (error) {
      console.error('Failed to add voice:', error);
    }
  };

  if (currentVoiceId) {
    const currentVoice = voices.find((v) => v.voiceId === currentVoiceId);
    return (
      <div className="flex items-center gap-2">
        <span className="px-4 py-2 bg-green-100 text-green-700 rounded-lg">
          ✓ Voice: {currentVoice?.name || currentVoiceId}
        </span>
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="text-sm text-blue-600 hover:text-blue-800 underline"
        >
          Change
        </button>
        {isOpen && (
          <VoiceDropdown
            voices={voices}
            isLoading={voicesLoading}
            onSelect={handleSelectVoice}
            onClose={() => setIsOpen(false)}
            showAddForm={showAddForm}
            setShowAddForm={setShowAddForm}
            newVoiceId={newVoiceId}
            setNewVoiceId={setNewVoiceId}
            newVoiceName={newVoiceName}
            setNewVoiceName={setNewVoiceName}
            onAddVoice={handleAddExistingVoice}
            isPending={assignVoice.isPending || createVoice.isPending}
          />
        )}
      </div>
    );
  }

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        disabled={assignVoice.isPending}
        className="px-4 py-2 bg-indigo-600 text-white font-medium rounded-lg hover:bg-indigo-700 disabled:opacity-50 flex items-center gap-2"
        data-testid="select-voice-button"
      >
        <svg
          className="w-5 h-5"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z"
          />
        </svg>
        {assignVoice.isPending ? 'Assigning...' : 'Use Existing Voice'}
      </button>

      {isOpen && (
        <VoiceDropdown
          voices={voices}
          isLoading={voicesLoading}
          onSelect={handleSelectVoice}
          onClose={() => setIsOpen(false)}
          showAddForm={showAddForm}
          setShowAddForm={setShowAddForm}
          newVoiceId={newVoiceId}
          setNewVoiceId={setNewVoiceId}
          newVoiceName={newVoiceName}
          setNewVoiceName={setNewVoiceName}
          onAddVoice={handleAddExistingVoice}
          isPending={assignVoice.isPending || createVoice.isPending}
        />
      )}
    </div>
  );
}

interface VoiceDropdownProps {
  voices: Voice[];
  isLoading: boolean;
  onSelect: (voice: Voice) => void;
  onClose: () => void;
  showAddForm: boolean;
  setShowAddForm: (show: boolean) => void;
  newVoiceId: string;
  setNewVoiceId: (id: string) => void;
  newVoiceName: string;
  setNewVoiceName: (name: string) => void;
  onAddVoice: (e: React.FormEvent) => void;
  isPending: boolean;
}

function VoiceDropdown({
  voices,
  isLoading,
  onSelect,
  onClose,
  showAddForm,
  setShowAddForm,
  newVoiceId,
  setNewVoiceId,
  newVoiceName,
  setNewVoiceName,
  onAddVoice,
  isPending,
}: VoiceDropdownProps) {
  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 z-10"
        onClick={onClose}
      />

      {/* Dropdown */}
      <div className="absolute top-full left-0 mt-2 w-80 bg-white rounded-lg shadow-lg border border-gray-200 z-20 max-h-96 overflow-auto">
        <div className="p-3 border-b border-gray-200">
          <h3 className="font-semibold text-gray-900">Select a Voice</h3>
          <p className="text-sm text-gray-500">Choose from previously cloned voices</p>
        </div>

        {isLoading ? (
          <div className="p-4 text-center text-gray-500">
            <div className="w-6 h-6 border-2 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-2" />
            Loading voices...
          </div>
        ) : voices.length === 0 && !showAddForm ? (
          <div className="p-4 text-center text-gray-500">
            <p className="mb-3">No saved voices yet.</p>
            <button
              onClick={() => setShowAddForm(true)}
              className="text-blue-600 hover:text-blue-800 underline text-sm"
            >
              Add an existing voice ID
            </button>
          </div>
        ) : (
          <div className="py-2">
            {voices.map((voice) => (
              <button
                key={voice.id}
                onClick={() => onSelect(voice)}
                disabled={isPending}
                className="w-full px-4 py-3 text-left hover:bg-gray-50 flex items-start gap-3 disabled:opacity-50"
                data-testid={`voice-option-${voice.voiceId}`}
              >
                <div className="w-8 h-8 bg-purple-100 rounded-full flex items-center justify-center flex-shrink-0">
                  <svg
                    className="w-4 h-4 text-purple-600"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z"
                    />
                  </svg>
                </div>
                <div className="flex-1 min-w-0">
                  <p className="font-medium text-gray-900 truncate">{voice.name}</p>
                  <p className="text-xs text-gray-500 truncate">{voice.voiceId}</p>
                  {voice.description && (
                    <p className="text-xs text-gray-400 truncate mt-1">
                      {voice.description}
                    </p>
                  )}
                </div>
              </button>
            ))}

            {!showAddForm && (
              <div className="px-4 py-2 border-t border-gray-100">
                <button
                  onClick={() => setShowAddForm(true)}
                  className="text-blue-600 hover:text-blue-800 text-sm flex items-center gap-1"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                  </svg>
                  Add existing voice ID
                </button>
              </div>
            )}
          </div>
        )}

        {showAddForm && (
          <form onSubmit={onAddVoice} className="p-4 border-t border-gray-200 bg-gray-50">
            <h4 className="font-medium text-gray-900 mb-3">Add Existing Voice</h4>
            <p className="text-xs text-gray-500 mb-3">
              Enter the MiniMax voice ID of a previously cloned voice
            </p>
            <div className="space-y-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Voice ID
                </label>
                <input
                  type="text"
                  value={newVoiceId}
                  onChange={(e) => setNewVoiceId(e.target.value)}
                  placeholder="e.g., test-voice-20260201133125"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  data-testid="new-voice-id-input"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Display Name
                </label>
                <input
                  type="text"
                  value={newVoiceName}
                  onChange={(e) => setNewVoiceName(e.target.value)}
                  placeholder="e.g., My Cloned Voice"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  data-testid="new-voice-name-input"
                />
              </div>
              <div className="flex gap-2">
                <button
                  type="submit"
                  disabled={!newVoiceId.trim() || !newVoiceName.trim() || isPending}
                  className="flex-1 px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 disabled:opacity-50"
                  data-testid="add-voice-button"
                >
                  {isPending ? 'Adding...' : 'Add & Use'}
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setShowAddForm(false);
                    setNewVoiceId('');
                    setNewVoiceName('');
                  }}
                  className="px-4 py-2 bg-gray-200 text-gray-700 text-sm font-medium rounded-lg hover:bg-gray-300"
                >
                  Cancel
                </button>
              </div>
            </div>
          </form>
        )}
      </div>
    </>
  );
}
