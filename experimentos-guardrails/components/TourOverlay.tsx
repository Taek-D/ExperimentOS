import React, { useEffect, useState, useCallback, useRef } from 'react';
import { createPortal } from 'react-dom';
import type { TourStep } from '../hooks/useTour';

interface TourOverlayProps {
  step: TourStep;
  currentIndex: number;
  totalSteps: number;
  onNext: () => void;
  onPrev: () => void;
  onSkip: () => void;
  onAction?: (action: string) => void;
}

interface TargetRect {
  top: number;
  left: number;
  width: number;
  height: number;
}

const SPOTLIGHT_PADDING = 12;
const TOOLTIP_GAP = 16;
const RAF_RETRY_LIMIT = 30; // ~500ms at 60fps

const TourOverlay: React.FC<TourOverlayProps> = ({
  step,
  currentIndex,
  totalSteps,
  onNext,
  onPrev,
  onSkip,
  onAction,
}) => {
  const [targetRect, setTargetRect] = useState<TargetRect | null>(null);
  const [tooltipPlacement, setTooltipPlacement] = useState<'bottom' | 'top'>('bottom');
  const retryCountRef = useRef(0);
  const rafIdRef = useRef<number>(0);
  const observerRef = useRef<ResizeObserver | null>(null);

  const measureTarget = useCallback(() => {
    if (!step.target) {
      setTargetRect(null);
      return true;
    }

    const el = document.querySelector(step.target);
    if (!el) return false;

    const rect = el.getBoundingClientRect();
    setTargetRect({
      top: rect.top + window.scrollY,
      left: rect.left + window.scrollX,
      width: rect.width,
      height: rect.height,
    });

    // Determine placement
    const spaceBelow = window.innerHeight - rect.bottom;
    setTooltipPlacement(spaceBelow > 280 ? 'bottom' : 'top');

    // Scroll into view
    el.scrollIntoView({ behavior: 'smooth', block: 'center' });

    return true;
  }, [step.target]);

  // Measure on step change with RAF retry for DOM transitions
  useEffect(() => {
    retryCountRef.current = 0;

    const tryMeasure = () => {
      if (measureTarget()) {
        retryCountRef.current = 0;
        return;
      }
      retryCountRef.current++;
      if (retryCountRef.current < RAF_RETRY_LIMIT) {
        rafIdRef.current = requestAnimationFrame(tryMeasure);
      }
    };

    rafIdRef.current = requestAnimationFrame(tryMeasure);

    return () => {
      if (rafIdRef.current) cancelAnimationFrame(rafIdRef.current);
    };
  }, [measureTarget, step.id]);

  // ResizeObserver for responsive repositioning
  useEffect(() => {
    if (!step.target) return;

    const el = document.querySelector(step.target);
    if (!el) return;

    observerRef.current = new ResizeObserver(() => {
      measureTarget();
    });
    observerRef.current.observe(el);

    const handleResize = () => measureTarget();
    window.addEventListener('resize', handleResize);
    window.addEventListener('scroll', handleResize, true);

    return () => {
      observerRef.current?.disconnect();
      window.removeEventListener('resize', handleResize);
      window.removeEventListener('scroll', handleResize, true);
    };
  }, [step.target, step.id, measureTarget]);

  const handleNext = () => {
    if (step.action && onAction) {
      onAction(step.action);
    }
    onNext();
  };

  const isFirstStep = currentIndex === 0;
  const isLastStep = currentIndex === totalSteps - 1;
  const isCenterModal = step.target === null;

  // Spotlight clip path for the overlay
  const spotlightStyle = targetRect
    ? {
        boxShadow: `0 0 0 0 transparent`,
        clipPath: `polygon(
          0% 0%,
          0% 100%,
          ${targetRect.left - SPOTLIGHT_PADDING}px 100%,
          ${targetRect.left - SPOTLIGHT_PADDING}px ${targetRect.top - SPOTLIGHT_PADDING}px,
          ${targetRect.left + targetRect.width + SPOTLIGHT_PADDING}px ${targetRect.top - SPOTLIGHT_PADDING}px,
          ${targetRect.left + targetRect.width + SPOTLIGHT_PADDING}px ${targetRect.top + targetRect.height + SPOTLIGHT_PADDING}px,
          ${targetRect.left - SPOTLIGHT_PADDING}px ${targetRect.top + targetRect.height + SPOTLIGHT_PADDING}px,
          ${targetRect.left - SPOTLIGHT_PADDING}px 100%,
          100% 100%,
          100% 0%
        )`,
      }
    : {};

  // Tooltip position
  const tooltipStyle = (): React.CSSProperties => {
    if (isCenterModal || !targetRect) {
      return {
        position: 'fixed',
        top: '50%',
        left: '50%',
        transform: 'translate(-50%, -50%)',
      };
    }

    const centerX = targetRect.left + targetRect.width / 2;
    const tooltipWidth = 380;
    let left = centerX - tooltipWidth / 2;

    // Keep tooltip within viewport
    left = Math.max(16, Math.min(left, window.innerWidth - tooltipWidth - 16));

    if (tooltipPlacement === 'bottom') {
      return {
        position: 'absolute',
        top: targetRect.top + targetRect.height + SPOTLIGHT_PADDING + TOOLTIP_GAP,
        left,
        width: tooltipWidth,
      };
    }
    return {
      position: 'absolute',
      top: targetRect.top - SPOTLIGHT_PADDING - TOOLTIP_GAP,
      left,
      width: tooltipWidth,
      transform: 'translateY(-100%)',
    };
  };

  const overlay = (
    <div className="fixed inset-0 z-[9999]" style={{ pointerEvents: 'auto' }}>
      {/* Dark overlay with spotlight cutout */}
      <div
        className="absolute inset-0 bg-black/70 transition-all duration-300"
        style={isCenterModal ? {} : spotlightStyle}
        onClick={onSkip}
      />

      {/* Spotlight border glow */}
      {targetRect && (
        <div
          className="absolute rounded-xl border-2 border-primary/50 pointer-events-none transition-all duration-300"
          style={{
            top: targetRect.top - SPOTLIGHT_PADDING,
            left: targetRect.left - SPOTLIGHT_PADDING,
            width: targetRect.width + SPOTLIGHT_PADDING * 2,
            height: targetRect.height + SPOTLIGHT_PADDING * 2,
            boxShadow: '0 0 20px rgba(59, 130, 246, 0.3), inset 0 0 20px rgba(59, 130, 246, 0.1)',
          }}
        />
      )}

      {/* Tooltip card */}
      <div
        style={tooltipStyle()}
        className="bg-surface-2 border border-primary/30 rounded-2xl p-6 shadow-2xl shadow-black/50 max-w-[380px] animate-in fade-in slide-in-from-bottom-2 duration-300"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Step indicator */}
        <div className="flex items-center justify-between mb-3">
          <div className="flex gap-1.5">
            {Array.from({ length: totalSteps }, (_, i) => (
              <div
                key={i}
                className={`h-1.5 rounded-full transition-all duration-300 ${
                  i === currentIndex
                    ? 'w-6 bg-primary'
                    : i < currentIndex
                      ? 'w-1.5 bg-primary/50'
                      : 'w-1.5 bg-white/20'
                }`}
              />
            ))}
          </div>
          <span className="text-xs text-white/40 font-mono">
            {currentIndex + 1}/{totalSteps}
          </span>
        </div>

        {/* Content */}
        <h3 className="text-lg font-bold text-white mb-2">{step.title}</h3>
        <p className="text-sm text-white/70 leading-relaxed mb-5">{step.description}</p>

        {/* Actions */}
        <div className="flex items-center justify-between">
          <button
            onClick={onSkip}
            className="text-xs text-white/40 hover:text-white/70 transition-colors"
          >
            Skip tour
          </button>
          <div className="flex gap-2">
            {!isFirstStep && (
              <button
                onClick={onPrev}
                className="px-3 py-1.5 text-sm text-white/70 hover:text-white bg-white/5 hover:bg-white/10 rounded-lg transition-all"
              >
                Back
              </button>
            )}
            <button
              onClick={handleNext}
              className="px-4 py-1.5 text-sm font-medium text-white bg-primary hover:bg-primary/80 rounded-lg transition-all shadow-lg shadow-primary/20"
            >
              {step.action === 'load-demo'
                ? 'Load Demo'
                : isLastStep
                  ? 'Finish'
                  : 'Next'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );

  return createPortal(overlay, document.body);
};

export default TourOverlay;
