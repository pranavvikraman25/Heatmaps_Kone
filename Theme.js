/**
 * KONE ELEVATOR MAINTENANCE - BACK REPORTING SYSTEM
 * Professional Industrial Design System
 * 
 * Color Palette: Enterprise Grade (No childish colors)
 * All colors are professional, minimalist, and suitable for industrial use
 */

export const COLORS = {
  // Primary - Dark Professional Blue (KONE Brand)
  primary: '#0a1929',        // Very Dark Blue-Black
  primaryLight: '#1a3a52',   // Dark Steel Blue
  primaryAccent: '#2e5090',  // Professional Blue
  
  // Secondary - Subtle Accent
  secondary: '#1976d2',      // Steel Blue
  secondaryLight: '#42a5f5', // Professional Light Blue
  
  // Status Colors - Professional
  success: '#2e7d32',        // Deep Green (not bright)
  warning: '#c87137',        // Industrial Orange-Brown
  danger: '#b71c1c',         // Industrial Red
  info: '#1565c0',           // Steel Blue
  
  // Neutral - Industrial Grays
  dark: '#0a0e27',           // Almost Black
  darkGray: '#1e293b',       // Dark Slate
  gray: '#475569',           // Professional Gray
  lightGray: '#94a3b8',      // Light Slate
  veryLight: '#e2e8f0',      // Off-white Border
  surface: '#f8fafc',        // Very Light Background
  white: '#ffffff',          // Pure White
  
  // Background
  background: '#fafbfc',     // Subtle light background
  
  // Heat Map Colors (Intensity-based)
  heatmapCold: '#cfe9ff',    // Light Blue (low intensity)
  heatmapMedium: '#42a5f5',  // Medium Blue
  heatmapHot: '#0a3d62',     // Dark Blue (high intensity)
  
  // Floor Visualization
  floorActive: '#2e5090',    // Deep Blue
  floorInactive: '#cbd5e1',  // Light Gray
  
  // Elevation/Height
  elevationHigh: '#0a3d62',
  elevationMid: '#1565c0',
  elevationLow: '#64b5f6',
};

export const TYPOGRAPHY = {
  // Font Families - Professional
  sans: 'System',
  mono: 'Courier New',
  
  // Sizes - Hierarchy
  h1: { fontSize: 28, fontWeight: '700', lineHeight: 36 },
  h2: { fontSize: 24, fontWeight: '700', lineHeight: 32 },
  h3: { fontSize: 20, fontWeight: '600', lineHeight: 28 },
  h4: { fontSize: 18, fontWeight: '600', lineHeight: 24 },
  h5: { fontSize: 16, fontWeight: '600', lineHeight: 22 },
  h6: { fontSize: 14, fontWeight: '600', lineHeight: 20 },
  
  body1: { fontSize: 14, fontWeight: '400', lineHeight: 22 },
  body2: { fontSize: 13, fontWeight: '400', lineHeight: 20 },
  
  label: { fontSize: 12, fontWeight: '500', lineHeight: 16 },
  caption: { fontSize: 11, fontWeight: '400', lineHeight: 14 },
  
  mono: { fontSize: 12, fontWeight: '500', lineHeight: 16 },
};

export const SPACING = {
  xs: 4,
  sm: 8,
  md: 12,
  lg: 16,
  xl: 24,
  xxl: 32,
  xxxl: 48,
};

export const RADIUS = {
  sm: 4,
  md: 6,
  lg: 8,
  xl: 12,
  xxl: 16,
};

export const SHADOWS = {
  none: {},
  sm: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.08,
    shadowRadius: 2,
    elevation: 1,
  },
  md: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.12,
    shadowRadius: 4,
    elevation: 2,
  },
  lg: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.16,
    shadowRadius: 8,
    elevation: 4,
  },
};

export const BORDERS = {
  thin: 0.5,
  regular: 1,
  thick: 2,
};

export default {
  COLORS,
  TYPOGRAPHY,
  SPACING,
  RADIUS,
  SHADOWS,
  BORDERS,
};
