import React, { useState, useRef, useCallback, useEffect, useMemo } from 'react';
import { createPortal } from 'react-dom';
import { getGlossaryEntry } from '../data/glossary';

interface GlossaryTermProps {
  termKey: string;
  children: React.ReactNode;
}

const GlossaryTerm: React.FC<GlossaryTermProps> = ({ termKey, children }) => {
  const [isVisible, setIsVisible] = useState(false);
  const [expanded, setExpanded] = useState(false);
  const [position, setPosition] = useState({ top: 0, left: 0, above: false });
  const triggerRef = useRef<HTMLSpanElement>(null);
  const tooltipRef = useRef<HTMLDivElement>(null);
  const hideTimeoutRef = useRef<ReturnType<typeof setTimeout>>();

  const entry = useMemo(() => getGlossaryEntry(termKey), [termKey]);

  const updatePosition = useCallback(() => {
    if (!triggerRef.current) return;
    const rect = triggerRef.current.getBoundingClientRect();
    const tooltipWidth = 320;

    let left = rect.left + rect.width / 2 - tooltipWidth / 2;
    left = Math.max(8, Math.min(left, window.innerWidth - tooltipWidth - 8));

    const spaceBelow = window.innerHeight - rect.bottom;
    const above = spaceBelow < 200;
    const top = above
      ? rect.top + window.scrollY - 8
      : rect.bottom + window.scrollY + 8;

    setPosition({ top, left, above });
  }, []);

  const show = useCallback(() => {
    if (hideTimeoutRef.current) clearTimeout(hideTimeoutRef.current);
    updatePosition();
    setIsVisible(true);
  }, [updatePosition]);

  const hide = useCallback(() => {
    hideTimeoutRef.current = setTimeout(() => {
      setIsVisible(false);
      setExpanded(false);
    }, 150);
  }, []);

  const cancelHide = useCallback(() => {
    if (hideTimeoutRef.current) clearTimeout(hideTimeoutRef.current);
  }, []);

  useEffect(() => {
    return () => {
      if (hideTimeoutRef.current) clearTimeout(hideTimeoutRef.current);
    };
  }, []);

  // Early return after all hooks
  if (!entry) return <>{children}</>;

  const tooltip = isVisible
    ? createPortal(
        <div
          ref={tooltipRef}
          className="fixed z-[9998] animate-in fade-in duration-150"
          style={{
            top: position.top,
            left: position.left,
            width: 320,
            transform: position.above ? 'translateY(-100%)' : undefined,
          }}
          onMouseEnter={cancelHide}
          onMouseLeave={hide}
        >
          <div className="bg-slate-900 border border-white/20 rounded-xl p-4 shadow-2xl shadow-black/50">
            <div className="text-xs font-bold text-primary uppercase tracking-wider mb-1">
              {entry.term}
            </div>
            <p className="text-sm text-white/80 leading-relaxed">
              {entry.shortDescription}
            </p>
            {expanded && (
              <p className="text-sm text-white/60 leading-relaxed mt-2 pt-2 border-t border-white/10">
                {entry.longDescription}
              </p>
            )}
            <button
              onClick={() => setExpanded(!expanded)}
              className="text-xs text-primary/70 hover:text-primary mt-2 transition-colors"
            >
              {expanded ? 'Less' : 'More'}
            </button>
          </div>
        </div>,
        document.body,
      )
    : null;

  return (
    <>
      <span
        ref={triggerRef}
        className="border-b border-dashed border-primary/40 cursor-help"
        onMouseEnter={show}
        onMouseLeave={hide}
      >
        {children}
      </span>
      {tooltip}
    </>
  );
};

export default GlossaryTerm;
