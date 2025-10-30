import { useState } from 'react';

export function useTheme() {
  const [theme, setTheme] = useState(() => {
    return localStorage.getItem('theme') ||
           (window.matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark');
  });

  const toggleTheme = () => {
    const newTheme = theme === 'dark' ? 'light' : 'dark';

    if (newTheme === 'light') {
      document.documentElement.setAttribute('data-theme', 'light');
    } else {
      document.documentElement.removeAttribute('data-theme');
    }

    localStorage.setItem('theme', newTheme);
    setTheme(newTheme);
  };

  return { theme, toggleTheme };
}
