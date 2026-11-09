import React from 'react';
import { Chip } from '@mui/material';

type BadgeVariant = 'cheapest' | 'expensive' | 'opportunity' | 'risk';

interface HeatBadgeProps {
  /** Alias for variant – kept for backward compatibility */
  type?: BadgeVariant;
  /** Preferred prop name */
  variant?: BadgeVariant;
  label?: string;
}

const variantColors: Record<BadgeVariant, { bg: string; text: string }> = {
  cheapest: { bg: '#e6f4ea', text: '#027a48' },
  expensive: { bg: '#fde7e9', text: '#b91c1c' },
  opportunity: { bg: '#fff4e5', text: '#d97706' },
  risk: { bg: '#fef2f2', text: '#991b1b' },
};

export const HeatBadge: React.FC<HeatBadgeProps> = ({ type, variant, label }) => {
  const badge = variant ?? type;
  if (!badge) return null;
  const colors = variantColors[badge];
  const chipLabel = label ?? badge.charAt(0).toUpperCase() + badge.slice(1);
  return (
    <Chip
      label={chipLabel}
      size="small"
      sx={{ backgroundColor: colors.bg, color: colors.text, fontWeight: 600, borderRadius: '4px' }}
    />
  );
};

export default HeatBadge;
