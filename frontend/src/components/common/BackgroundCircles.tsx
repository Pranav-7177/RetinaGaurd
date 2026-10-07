import React from 'react';
import { motion, useReducedMotion } from 'framer-motion';
import clsx from 'clsx';

export interface BackgroundCirclesProps {
  children?: React.ReactNode;
  className?: string;
}

export const BackgroundCircles: React.FC<BackgroundCirclesProps> = ({
  children,
  className,
}) => {
  const shouldReduceMotion = useReducedMotion();

  return (
    <div
      className={clsx(
        'relative w-full flex items-center justify-center overflow-hidden',
        className
      )}
    >
      {/* Ambient Central Radial Glow */}
      <div
        className="pointer-events-none absolute inset-0 flex items-center justify-center"
        aria-hidden="true"
      >
        <div className="w-[500px] h-[500px] rounded-full bg-gradient-to-tr from-teal-500/15 via-cyan-500/10 to-transparent blur-3xl opacity-70" />
        <div className="w-[300px] h-[300px] rounded-full bg-teal-400/10 blur-2xl opacity-60" />
      </div>

      {/* Optical Reticle / Crosshair Guides (Subtle Clinical Fundus Camera Alignment) */}
      <div
        className="pointer-events-none absolute inset-0 flex items-center justify-center opacity-25"
        aria-hidden="true"
      >
        {/* Horizontal crosshair */}
        <div className="w-full max-w-4xl h-[1px] bg-gradient-to-r from-transparent via-teal-400/40 to-transparent" />
        {/* Vertical crosshair */}
        <div className="absolute h-full max-h-[600px] w-[1px] bg-gradient-to-b from-transparent via-cyan-400/40 to-transparent" />
      </div>

      {/* Concentric Animated Retinal Rings */}
      <div
        className="pointer-events-none absolute inset-0 flex items-center justify-center"
        aria-hidden="true"
      >
        {/* Ring 1: Inner Core (280px) */}
        <motion.div
          animate={
            shouldReduceMotion
              ? undefined
              : {
                  rotate: 360,
                  scale: [1, 1.02, 1],
                }
          }
          transition={{
            rotate: { duration: 50, repeat: Infinity, ease: 'linear' },
            scale: { duration: 6, repeat: Infinity, ease: 'easeInOut' },
          }}
          className="absolute w-[260px] h-[260px] sm:w-[300px] sm:h-[300px] rounded-full border border-teal-500/25 flex items-center justify-center"
        >
          {/* Orbital Satellite Node */}
          <div className="absolute -top-1 w-2 h-2 rounded-full bg-teal-400 shadow-[0_0_8px_rgba(45,212,191,0.8)]" />
        </motion.div>

        {/* Ring 2: Mid Ring (460px) */}
        <motion.div
          animate={
            shouldReduceMotion
              ? undefined
              : {
                  rotate: -360,
                }
          }
          transition={{
            duration: 70,
            repeat: Infinity,
            ease: 'linear',
          }}
          className="absolute w-[420px] h-[420px] sm:w-[480px] sm:h-[480px] rounded-full border border-cyan-500/20"
        >
          <div className="absolute -bottom-1.5 right-1/4 w-2.5 h-2.5 rounded-full bg-cyan-400/80 shadow-[0_0_10px_rgba(34,211,238,0.7)]" />
        </motion.div>

        {/* Ring 3: Dashed Clinical Optical Guide (660px) */}
        <motion.div
          animate={
            shouldReduceMotion
              ? undefined
              : {
                  rotate: 360,
                }
          }
          transition={{
            duration: 100,
            repeat: Infinity,
            ease: 'linear',
          }}
          className="absolute w-[580px] h-[580px] sm:w-[680px] sm:h-[680px] rounded-full border border-dashed border-teal-400/20"
        >
          <div className="absolute top-1/3 -left-1 w-2 h-2 rounded-full bg-emerald-400/70" />
        </motion.div>

        {/* Ring 4: Outer Horizon (880px) */}
        <motion.div
          animate={
            shouldReduceMotion
              ? undefined
              : {
                  scale: [1, 1.015, 1],
                }
          }
          transition={{
            duration: 8,
            repeat: Infinity,
            ease: 'easeInOut',
          }}
          className="absolute w-[760px] h-[760px] sm:w-[900px] sm:h-[900px] rounded-full border border-teal-500/10"
        />

        {/* Ring 5: Ambient Boundary (1100px) */}
        <div className="absolute w-[940px] h-[940px] sm:w-[1140px] sm:h-[1140px] rounded-full border border-slate-700/20" />
      </div>

      {/* Foreground Content */}
      <div className="relative z-10 w-full">{children}</div>
    </div>
  );
};

export default BackgroundCircles;
