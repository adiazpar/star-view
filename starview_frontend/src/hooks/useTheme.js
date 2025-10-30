import { useState, useEffect } from 'react';

export function useTheme() {
  // Initialize theme by checking what's already applied to the document
  // (the inline script in index.html has already set this)
  const [theme, setTheme] = useState(() => {
    const hasLightTheme = document.documentElement.hasAttribute('data-theme');
    return hasLightTheme ? 'light' : 'dark';
  });

  // Apply theme to document when theme changes (not on initial mount)
  useEffect(() => {
    if (theme === 'light') {
      document.documentElement.setAttribute('data-theme', 'light');
    } else {
      document.documentElement.removeAttribute('data-theme');
    }
  }, [theme]);

  const toggleTheme = () => {
    const newTheme = theme === 'dark' ? 'light' : 'dark';
    localStorage.setItem('theme', newTheme);
    setTheme(newTheme);
  };

  return { theme, toggleTheme };
}
