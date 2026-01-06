/**
 * ColorPicker component for selecting hex colors.
 *
 * Provides dual input methods:
 * - HTML5 color picker for visual selection
 * - Text input for direct hex code entry (#RRGGBB)
 *
 * Validates hex color format and synchronizes both inputs.
 */

import { useState, useEffect } from 'react';
import './ColorPicker.css';

interface ColorPickerProps {
  label: string;
  value: string;
  onChange: (color: string) => void;
}

export function ColorPicker({ label, value, onChange }: ColorPickerProps) {
  const [hexInput, setHexInput] = useState(value);
  const [isValid, setIsValid] = useState(true);
  const [isTransparent, setIsTransparent] = useState(value === 'transparent');

  // Sync hexInput when value prop changes
  useEffect(() => {
    if (value === 'transparent') {
      setIsTransparent(true);
      setHexInput('#FFFFFF');
      setIsValid(true);
    } else {
      setIsTransparent(false);
      setHexInput(value);
      setIsValid(isValidHexColor(value));
    }
  }, [value]);

  /**
   * Validates hex color format (#RRGGBB).
   */
  const isValidHexColor = (color: string): boolean => {
    return /^#[0-9A-Fa-f]{6}$/.test(color);
  };

  /**
   * Handle transparent checkbox toggle.
   */
  const handleTransparentToggle = (e: React.ChangeEvent<HTMLInputElement>) => {
    const checked = e.target.checked;
    setIsTransparent(checked);
    if (checked) {
      onChange('transparent');
    } else {
      onChange(hexInput);
    }
  };

  /**
   * Handle HTML5 color input change.
   * Always valid since browser enforces format.
   */
  const handleColorChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newColor = e.target.value.toUpperCase();
    setHexInput(newColor);
    setIsValid(true);
    setIsTransparent(false);
    onChange(newColor);
  };

  /**
   * Handle text input change with validation.
   * Only propagate valid colors to parent.
   */
  const handleHexInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const inputValue = e.target.value;
    setHexInput(inputValue);

    const valid = isValidHexColor(inputValue);
    setIsValid(valid);

    if (valid) {
      setIsTransparent(false);
      onChange(inputValue.toUpperCase());
    }
  };

  /**
   * Auto-format hex input on blur if missing '#' prefix.
   */
  const handleHexInputBlur = () => {
    if (hexInput && !hexInput.startsWith('#')) {
      const formatted = `#${hexInput}`;
      if (isValidHexColor(formatted)) {
        setHexInput(formatted);
        setIsValid(true);
        setIsTransparent(false);
        onChange(formatted.toUpperCase());
      }
    }
  };

  return (
    <div className="color-picker">
      <label className="color-picker-label">{label}</label>
      <div className="color-picker-inputs">
        <input
          type="color"
          value={isTransparent ? '#FFFFFF' : value}
          onChange={handleColorChange}
          className="color-picker-visual"
          title={`Select ${label.toLowerCase()}`}
          disabled={isTransparent}
        />
        <input
          type="text"
          value={hexInput}
          onChange={handleHexInputChange}
          onBlur={handleHexInputBlur}
          placeholder="#FFFFFF"
          maxLength={7}
          className={`color-picker-text ${!isValid ? 'color-picker-text-invalid' : ''}`}
          title="Enter hex color code (e.g., #1976D2)"
          disabled={isTransparent}
        />
        <label className="color-picker-transparent-label">
          <input
            type="checkbox"
            checked={isTransparent}
            onChange={handleTransparentToggle}
            className="color-picker-checkbox"
          />
          <span>Transparent</span>
        </label>
        {!isValid && (
          <span className="color-picker-error">
            Invalid hex color format. Use #RRGGBB (e.g., #1976D2)
          </span>
        )}
      </div>
    </div>
  );
}
