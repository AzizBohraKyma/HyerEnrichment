import { RequestedTier } from '@/src/lib/types';
import { tierLabels } from '@/src/lib/utils';

export const ALL_TIERS: RequestedTier[] = ['tier1', 'tier2', 'tier3', 'tier4'];

export function parseTiersFromQuery(value: string | null): RequestedTier[] {
  if (!value) {
    return [];
  }

  return value
    .split(',')
    .map((tier) => tier.trim())
    .filter((tier): tier is RequestedTier =>
      tier === 'tier1' || tier === 'tier2' || tier === 'tier3' || tier === 'tier4',
    );
}

export function tiersToQuery(tiers: RequestedTier[]): string {
  return tiers.join(',');
}

export function getTierLabel(tier: RequestedTier): string {
  return tierLabels[tier] ?? tier;
}

export function availableTiersForMode(mode: 'async' | 'sync'): RequestedTier[] {
  if (mode === 'sync') {
    return ALL_TIERS.filter((tier) => tier !== 'tier1');
  }
  return ALL_TIERS;
}

export function hasValidTierSelection(tiers: RequestedTier[], mode: 'async' | 'sync'): boolean {
  const allowed = availableTiersForMode(mode);
  return tiers.some((tier) => allowed.includes(tier));
}
