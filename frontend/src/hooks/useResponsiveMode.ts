import { useEffect, useMemo, useState } from 'react';

export type DeviceType = 'phone' | 'tablet' | 'other' | 'unknown';
export type OrientationType = 'portrait' | 'landscape' | 'unknown';

export interface ResponsiveMode {
  deviceType: DeviceType;
  orientation: OrientationType;
  isPortraitTouch: boolean;
  isFallback: boolean;
  viewportWidth: number;
}

const PHONE_MAX_WIDTH = 499;
const TABLET_MAX_WIDTH = 1024;

function computeResponsiveMode(): ResponsiveMode {
  if (typeof window === 'undefined' || typeof window.matchMedia !== 'function') {
    return {
      deviceType: 'unknown',
      orientation: 'unknown',
      isPortraitTouch: false,
      isFallback: true,
      viewportWidth: 0,
    };
  }

  const portraitQuery = window.matchMedia('(orientation: portrait)');
  const coarsePointerQuery = window.matchMedia('(pointer: coarse)');
  const width = window.innerWidth || document.documentElement.clientWidth || 0;
  const height = window.innerHeight || document.documentElement.clientHeight || 0;
  const shortEdge = width > 0 && height > 0 ? Math.min(width, height) : width;

  const orientation: OrientationType = portraitQuery.matches
    ? 'portrait'
    : 'landscape';
  const hasCoarsePointer = coarsePointerQuery.matches;

  let deviceType: DeviceType = 'other';
  if (shortEdge > 0 && shortEdge <= PHONE_MAX_WIDTH) {
    deviceType = 'phone';
  } else if (shortEdge > PHONE_MAX_WIDTH && shortEdge <= TABLET_MAX_WIDTH) {
    deviceType = 'tablet';
  } else {
    deviceType = 'other';
  }

  const isPortraitTouch =
    hasCoarsePointer &&
    orientation === 'portrait' &&
    (deviceType === 'phone' || deviceType === 'tablet');

  return {
    deviceType,
    orientation,
    isPortraitTouch,
    isFallback: false,
    viewportWidth: width,
  };
}

export function useResponsiveMode(): ResponsiveMode {
  const [mode, setMode] = useState<ResponsiveMode>(() => computeResponsiveMode());

  useEffect(() => {
    if (typeof window === 'undefined' || typeof window.matchMedia !== 'function') {
      return;
    }

    let rafId: number | null = null;
    const portraitQuery = window.matchMedia('(orientation: portrait)');
    const coarsePointerQuery = window.matchMedia('(pointer: coarse)');

    const updateMode = () => {
      if (rafId !== null) {
        window.cancelAnimationFrame(rafId);
      }
      rafId = window.requestAnimationFrame(() => {
        setMode(computeResponsiveMode());
      });
    };

    const addListener = (mediaQuery: MediaQueryList, listener: () => void) => {
      if (typeof mediaQuery.addEventListener === 'function') {
        mediaQuery.addEventListener('change', listener);
        return () => mediaQuery.removeEventListener('change', listener);
      }
      mediaQuery.addListener(listener);
      return () => mediaQuery.removeListener(listener);
    };

    const removePortrait = addListener(portraitQuery, updateMode);
    const removeCoarsePointer = addListener(coarsePointerQuery, updateMode);
    window.addEventListener('resize', updateMode);

    return () => {
      if (rafId !== null) {
        window.cancelAnimationFrame(rafId);
      }
      removePortrait();
      removeCoarsePointer();
      window.removeEventListener('resize', updateMode);
    };
  }, []);

  return useMemo(() => mode, [mode]);
}
