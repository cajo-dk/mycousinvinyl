/**
 * Simple SVG icon wrapper for Material Design Icons.
 */

import './Icon.css';

interface IconProps {
  path: string;
  size?: number;
  className?: string;
  title?: string;
  color?: string;
}

export function Icon({ path, size = 18, className = '', title, color }: IconProps) {
  const ariaHidden = title ? undefined : true;
  const role = title ? 'img' : 'presentation';

  return (
    <svg
      className={`icon ${className}`}
      viewBox="0 0 24 24"
      width={size}
      height={size}
      aria-hidden={ariaHidden}
      role={role}
      style={color ? { fill: color } : undefined}
    >
      {title && <title>{title}</title>}
      <path d={path} />
    </svg>
  );
}
