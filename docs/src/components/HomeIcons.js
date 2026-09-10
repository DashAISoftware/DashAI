import React from "react";

// Stroke-based 24x24 inline SVGs. Each inherits `currentColor` from the
// card icon box (color: var(--card-accent)), so no per-icon color is needed.
// Shared by the English and Spanish home pages to prevent markup drift.

const svgProps = {
  viewBox: "0 0 24 24",
  fill: "none",
  stroke: "currentColor",
  strokeWidth: 2,
  strokeLinecap: "round",
  strokeLinejoin: "round",
  "aria-hidden": true,
};

export const ICONS = {
  // Discover - compass
  discover: (
    <svg {...svgProps}>
      <circle cx="12" cy="12" r="10" />
      <path d="m16.24 7.76-2.12 6.36-6.36 2.12 2.12-6.36 6.36-2.12z" />
    </svg>
  ),
  // Learn - graduation cap
  learn: (
    <svg {...svgProps}>
      <path d="M22 10 12 5 2 10l10 5 10-5z" />
      <path d="M6 12v5c0 1 2.5 2.5 6 2.5s6-1.5 6-2.5v-5" />
    </svg>
  ),
  // Deep Dive - layers / architecture
  "deep-dive": (
    <svg {...svgProps}>
      <path d="m12 2 9 5-9 5-9-5 9-5z" />
      <path d="m3 12 9 5 9-5" />
      <path d="m3 17 9 5 9-5" />
    </svg>
  ),
  // Build - terminal / code
  build: (
    <svg {...svgProps}>
      <path d="m7 8 4 4-4 4" />
      <path d="M13 16h4" />
      <rect x="2" y="3" width="20" height="18" rx="2" />
    </svg>
  ),
};

// Decorative brand isotype, used as a faint background watermark.
// Inherits `currentColor`; opacity/size/rotation come from CSS.
export function Watermark({ className }) {
  return (
    <svg
      className={className}
      viewBox="0 0 218.96 237.04"
      fill="currentColor"
      aria-hidden="true"
    >
      <path d="M8.6 237.01C6.24 237.01 4.13 236.15 2.5 234.51C0.86 232.87 0.0 230.73 0.0 228.34L0.0 195.85C0.0 190.94 3.97 186.54 8.85 186.03L97.57 176.81C102.82 176.27 106.81 171.82 106.81 166.52L106.81 150.19C106.81 147.26 105.58 144.47 103.41 142.51C101.51 140.79 99.04 139.84 96.51 139.84C96.16 139.84 95.8 139.86 95.45 139.9L9.57 148.82C9.25 148.85 8.93 148.87 8.61 148.87C6.25 148.87 4.14 148.01 2.51 146.37C0.87 144.73 0.01 142.6 0.01 140.2L0.01 107.71C0.01 102.8 3.98 98.4 8.86 97.89L97.58 88.67C102.83 88.13 106.82 83.68 106.82 78.38L106.82 62.05C106.82 59.12 105.59 56.33 103.42 54.37C101.52 52.65 99.05 51.7 96.52 51.7C96.17 51.7 95.81 51.73 95.46 51.76L9.56 60.71C9.24 60.75 8.91 60.77 8.6 60.77C6.24 60.77 4.13 59.9 2.5 58.27C0.86 56.62 0.0 54.49 0.0 52.09L0.0 19.6C0.0 14.7 3.97 10.29 8.85 9.78L102.6 0.05C102.92 0.02 103.23 0.0 103.56 0.0C105.92 0.0 108.03 0.86 109.66 2.5C111.3 4.15 112.16 6.27 112.16 8.68L112.16 31.65C112.16 34.58 113.39 37.37 115.56 39.33C117.46 41.05 119.93 42.0 122.46 42.0C122.82 42.0 123.17 41.98 123.52 41.94L209.4 33.02C209.73 32.99 210.05 32.97 210.36 32.97C212.72 32.97 214.83 33.83 216.46 35.47C218.1 37.11 218.96 39.24 218.96 41.64L218.96 74.13C218.96 79.04 214.99 83.44 210.11 83.95L121.39 93.17C116.14 93.71 112.15 98.16 112.15 103.46L112.15 119.79C112.15 122.72 113.38 125.51 115.55 127.47C117.45 129.19 119.92 130.14 122.45 130.14C122.81 130.14 123.16 130.12 123.51 130.08L209.39 121.16C209.72 121.13 210.03 121.11 210.35 121.11C212.71 121.11 214.82 121.97 216.45 123.61C218.09 125.25 218.95 127.38 218.95 129.78L218.95 162.27C218.95 167.17 214.98 171.58 210.1 172.09L121.38 181.31C116.13 181.85 112.14 186.3 112.14 191.6L112.14 217.43C112.14 222.34 108.16 226.74 103.29 227.25L9.54 236.99C9.22 237.02 8.9 237.04 8.58 237.04L8.6 237.01Z" />
    </svg>
  );
}

export default ICONS;
