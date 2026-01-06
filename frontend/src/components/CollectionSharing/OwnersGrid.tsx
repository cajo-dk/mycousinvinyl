/**
 * OwnersGrid component for displaying item ownership.
 *
 * Displays a 2×2 grid showing:
 * - Position [0,0]: Current user (if they own it)
 * - Positions [0,1], [1,0], [1,1]: Up to 3 followed users
 *
 * Features:
 * - Custom icon colors from user preferences
 * - Numeric badge if user owns multiple copies
 * - Empty cells are transparent
 * - Tooltip showing user name on hover
 */

import { useMemo } from 'react';
import { Icon } from '@/components/UI';
import * as mdi from '@mdi/js';
import { UserOwnerInfo } from '@/types/api';
import './OwnersGrid.css';

interface OwnersGridProps {
  owners: UserOwnerInfo[];
  currentUserId: string;
  showEmpty?: boolean;
  className?: string;
}

interface GridCell {
  owner: UserOwnerInfo | null;
  position: number;
}

export function OwnersGrid({
  owners,
  currentUserId,
  showEmpty = false,
  className = '',
}: OwnersGridProps) {
  /**
   * Organize owners into grid positions.
   * [0] = Current user (top-left)
   * [1-3] = Followed users (top-right, bottom-left, bottom-right)
   */
  const gridCells = useMemo((): GridCell[] => {
    const cells: GridCell[] = [
      { owner: null, position: 0 },
      { owner: null, position: 1 },
      { owner: null, position: 2 },
      { owner: null, position: 3 },
    ];

    if (!owners || owners.length === 0) {
      return cells;
    }

    // Find current user
    const currentUserOwner = owners.find(o => o.user_id === currentUserId);
    if (currentUserOwner) {
      cells[0].owner = currentUserOwner;
    }

    // Add followed users (up to 3)
    const followedOwners = owners.filter(o => o.user_id !== currentUserId);
    for (let i = 0; i < Math.min(3, followedOwners.length); i++) {
      cells[i + 1].owner = followedOwners[i];
    }

    return cells;
  }, [owners, currentUserId]);

  /**
   * Get MDI icon path from icon type name.
   */
  const getIconPath = (iconType: string): string | null => {
    if (typeof iconType !== 'string') {
      return null;
    }
    const normalized = iconType.charAt(0).toLowerCase() + iconType.slice(1);
    return (mdi as any)[normalized] || (mdi as any)[iconType] || null;
  };

  /**
   * Check if grid has any owners.
   */
  const hasOwners = gridCells.some(cell => cell.owner !== null);

  if (!hasOwners && !showEmpty) {
    return null; // Don't render empty grid
  }

  return (
    <div className={`owners-grid ${className}`.trim()}>
      {gridCells.map((cell) => (
        <div key={cell.position} className="owners-grid-cell">
          {cell.owner ? (
            <div
              className="owners-grid-icon"
              style={{ backgroundColor: cell.owner.icon_bg_color }}
              title={`${cell.owner.display_name}${cell.owner.copy_count > 1 ? ` (${cell.owner.copy_count} copies)` : ''}`}
            >
              {getIconPath(cell.owner.icon_type) ? (
                <Icon
                  path={getIconPath(cell.owner.icon_type) as string}
                  size={25}
                  color={cell.owner.icon_fg_color}
                />
              ) : (
                <span
                  className="owners-grid-fallback"
                  style={{ color: cell.owner.icon_fg_color }}
                >
                  {(cell.owner.first_name || cell.owner.display_name || '?').charAt(0).toUpperCase()}
                </span>
              )}
              {cell.owner.copy_count > 1 && (
                <span className="owners-grid-badge">{cell.owner.copy_count}</span>
              )}
            </div>
          ) : (
            <div className="owners-grid-empty" />
          )}
        </div>
      ))}
    </div>
  );
}
