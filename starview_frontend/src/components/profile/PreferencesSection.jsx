import { useState } from 'react';
import { useTheme } from '../../hooks/useTheme';
import Alert from '../Alert';
import CollapsibleSection from './CollapsibleSection';
import './PreferencesSection.css';

/**
 * PreferencesSection - User preferences component
 *
 * Allows users to change theme (Light/Dark/Auto)
 */
function PreferencesSection() {
  const { theme, setThemeMode } = useTheme();
  const [success, setSuccess] = useState('');

  const handleThemeChange = (newTheme) => {
    setThemeMode(newTheme);
    setSuccess(`Theme changed to ${newTheme.charAt(0).toUpperCase() + newTheme.slice(1)} mode`);
  };

  return (
    <CollapsibleSection title="Preferences" defaultExpanded={false}>
      {/* Success Message */}
      {success && (
        <Alert
          type="success"
          message={success}
          onClose={() => setSuccess('')}
        />
      )}

      {/* Theme Selection */}
      <div>
        <label className="form-label preference-label">
          <i className="fa-solid fa-palette"></i> Theme
        </label>
        <div className="theme-selector">
          <button
            className={`theme-option ${theme === 'light' ? 'active' : ''}`}
            onClick={() => handleThemeChange('light')}
            type="button"
          >
            <i className="fa-solid fa-sun"></i>
            <span>Light</span>
          </button>
          <button
            className={`theme-option ${theme === 'dark' ? 'active' : ''}`}
            onClick={() => handleThemeChange('dark')}
            type="button"
          >
            <i className="fa-solid fa-moon"></i>
            <span>Dark</span>
          </button>
          <button
            className={`theme-option ${theme === 'auto' ? 'active' : ''}`}
            onClick={() => handleThemeChange('auto')}
            type="button"
          >
            <i className="fa-solid fa-circle-half-stroke"></i>
            <span>Auto</span>
          </button>
        </div>
        <p className="preference-hint">
          <i className="fa-solid fa-circle-info"></i> Auto mode follows your system preferences
        </p>
      </div>
    </CollapsibleSection>
  );
}

export default PreferencesSection;
