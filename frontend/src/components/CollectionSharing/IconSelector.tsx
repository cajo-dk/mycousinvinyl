/**
 * IconSelector component for choosing collection sharing icon type.
 *
 * Displays 5 MDI alpha icon variants based on the user's first name initial:
 * - mdiAlpha{X}
 * - mdiAlpha{X}Box
 * - mdiAlpha{X}BoxOutline
 * - mdiAlpha{X}Circle
 * - mdiAlpha{X}CircleOutline
 */

import { useState, useEffect } from 'react';
import { Icon } from '@/components/UI';
import * as mdi from '@mdi/js';
import './IconSelector.css';

interface IconSelectorProps {
  firstName: string;
  selectedIcon: string;
  fgColor: string;
  bgColor: string;
  onChange: (iconType: string) => void;
}

export function IconSelector({
  firstName,
  selectedIcon,
  fgColor,
  bgColor,
  onChange
}: IconSelectorProps) {
  const [iconOptions, setIconOptions] = useState<Array<{ name: string; path: string }>>([]);

  useEffect(() => {
    // Extract first letter from first name
    const firstLetter = (firstName || 'A').charAt(0).toUpperCase();

    // Generate 5 icon type names
    const iconTypes = [
      `mdiAlpha${firstLetter}`,
      `mdiAlpha${firstLetter}Box`,
      `mdiAlpha${firstLetter}BoxOutline`,
      `mdiAlpha${firstLetter}Circle`,
      `mdiAlpha${firstLetter}CircleOutline`,
    ];

    // Map to icon paths from @mdi/js
    const options = iconTypes.map(name => ({
      name,
      path: (mdi as any)[name] || mdi.mdiAlpha, // Fallback to mdiAlpha if not found
    }));

    setIconOptions(options);
  }, [firstName]);

  return (
    <div className="icon-selector">
      <label className="icon-selector-label">Icon Style</label>
      <div className="icon-selector-options">
        {iconOptions.map(({ name, path }) => (
          <label key={name} className="icon-selector-option">
            <input
              type="radio"
              name="icon-type"
              value={name}
              checked={selectedIcon === name}
              onChange={() => onChange(name)}
              className="icon-selector-radio"
            />
            <div
              className="icon-selector-preview"
              style={{ backgroundColor: bgColor }}
            >
              <Icon
                path={path}
                size={40}
                color={fgColor}
              />
            </div>
            <span className="icon-selector-name">
              {name.replace('mdiAlpha', '').replace(/([A-Z])/g, ' $1').trim() || 'Basic'}
            </span>
          </label>
        ))}
      </div>
    </div>
  );
}
