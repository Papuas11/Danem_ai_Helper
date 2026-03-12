import './globals.css';
import React from 'react';

export const metadata = { title: 'DANEM Sales Copilot' };

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ru">
      <body>{children}</body>
    </html>
  );
}
