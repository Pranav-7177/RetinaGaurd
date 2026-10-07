import React, { useState, useRef } from 'react';
import { ZoomIn, ZoomOut, RotateCcw, Layers, Eye, Maximize2, Sparkles, Target, AlertTriangle } from 'lucide-react';
import { LesionFinding, RetinalStructure } from '../../types';

interface ImageZoomViewerProps {
  imageUrl: string;
  enhancedImageUrl?: string;
  title?: string;
  structures?: RetinalStructure;
  lesions?: LesionFinding[];
  showGradcam?: boolean;
  gradcamOpacity?: number;
  highlightLesionId?: string;
  onSelectLesion?: (lesion: LesionFinding) => void;
  className?: string;
}

export const ImageZoomViewer: React.FC<ImageZoomViewerProps> = ({
  imageUrl,
  enhancedImageUrl,
  title,
  structures,
  lesions = [],
  showGradcam = false,
  gradcamOpacity = 0.55,
  highlightLesionId,
  onSelectLesion,
  className = '',
}) => {
  const [zoom, setZoom] = useState(1);
  const [position, setPosition] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });

  // Layer Toggles
  const [showEnhanced, setShowEnhanced] = useState(false);
  const [showStructures, setShowStructures] = useState(true);
  const [showLesions, setShowLesions] = useState(true);
  const [showHeatmap, setShowHeatmap] = useState(showGradcam);
  const [splitMode, setSplitMode] = useState(false);
  const [splitPosition, setSplitPosition] = useState(50); // percentage

  const containerRef = useRef<HTMLDivElement>(null);

  const handleZoomIn = () => setZoom((prev) => Math.min(prev + 0.25, 4));
  const handleZoomOut = () => setZoom((prev) => Math.max(prev - 0.25, 0.75));
  const handleReset = () => {
    setZoom(1);
    setPosition({ x: 0, y: 0 });
  };

  const handleMouseDown = (e: React.MouseEvent) => {
    setIsDragging(true);
    setDragStart({ x: e.clientX - position.x, y: e.clientY - position.y });
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!isDragging) return;
    setPosition({
      x: e.clientX - dragStart.x,
      y: e.clientY - dragStart.y,
    });
  };

  const handleMouseUp = () => setIsDragging(false);

  const activeImage = showEnhanced && enhancedImageUrl ? enhancedImageUrl : imageUrl;

  return (
    <div className={`relative flex flex-col bg-navy-950 rounded-2xl border border-slate-800 overflow-hidden select-none shadow-xl ${className}`}>
      {/* Viewer Header / Toolbar */}
      <div className="flex flex-wrap items-center justify-between px-4 py-3 bg-navy-900/90 border-b border-slate-800 text-slate-200 z-10 gap-2">
        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold uppercase tracking-wider text-teal-400">
            {title || 'Retinal Fundus Viewport'}
          </span>
          <span className="text-[11px] text-slate-400 font-mono">Zoom: {Math.round(zoom * 100)}%</span>
        </div>

        {/* Layer Controls */}
        <div className="flex items-center gap-1.5 flex-wrap">
          {enhancedImageUrl && (
            <button
              onClick={() => setShowEnhanced(!showEnhanced)}
              className={`px-2.5 py-1 text-xs font-medium rounded-lg border transition-all flex items-center gap-1.5 ${
                showEnhanced
                  ? 'bg-teal-900/60 border-teal-500 text-teal-200'
                  : 'bg-navy-800 border-slate-700 text-slate-300 hover:bg-slate-700'
              }`}
              title="Toggle CLAHE Enhancement"
            >
              <Sparkles className="w-3.5 h-3.5" />
              <span>CLAHE</span>
            </button>
          )}

          {structures && (
            <button
              onClick={() => setShowStructures(!showStructures)}
              className={`px-2.5 py-1 text-xs font-medium rounded-lg border transition-all flex items-center gap-1.5 ${
                showStructures
                  ? 'bg-blue-900/60 border-blue-500 text-blue-200'
                  : 'bg-navy-800 border-slate-700 text-slate-300 hover:bg-slate-700'
              }`}
              title="Toggle Retinal Landmarks (Disc & Macula)"
            >
              <Target className="w-3.5 h-3.5" />
              <span>Landmarks</span>
            </button>
          )}

          {lesions.length > 0 && (
            <button
              onClick={() => setShowLesions(!showLesions)}
              className={`px-2.5 py-1 text-xs font-medium rounded-lg border transition-all flex items-center gap-1.5 ${
                showLesions
                  ? 'bg-rose-900/60 border-rose-500 text-rose-200'
                  : 'bg-navy-800 border-slate-700 text-slate-300 hover:bg-slate-700'
              }`}
              title="Toggle Lesion Detection Boxes"
            >
              <AlertTriangle className="w-3.5 h-3.5" />
              <span>Lesions ({lesions.length})</span>
            </button>
          )}

          <button
            onClick={() => setShowHeatmap(!showHeatmap)}
            className={`px-2.5 py-1 text-xs font-medium rounded-lg border transition-all flex items-center gap-1.5 ${
              showHeatmap
                ? 'bg-amber-900/60 border-amber-500 text-amber-200'
                : 'bg-navy-800 border-slate-700 text-slate-300 hover:bg-slate-700'
            }`}
            title="Toggle Grad-CAM Saliency Heatmap"
          >
            <Layers className="w-3.5 h-3.5" />
            <span>Grad-CAM</span>
          </button>
        </div>

        {/* Zoom Action Tools */}
        <div className="flex items-center gap-1 bg-navy-800/80 p-1 rounded-lg border border-slate-700">
          <button
            onClick={handleZoomIn}
            className="p-1 text-slate-300 hover:text-white hover:bg-slate-700 rounded transition-colors"
            title="Zoom In"
          >
            <ZoomIn className="w-4 h-4" />
          </button>
          <button
            onClick={handleZoomOut}
            className="p-1 text-slate-300 hover:text-white hover:bg-slate-700 rounded transition-colors"
            title="Zoom Out"
          >
            <ZoomOut className="w-4 h-4" />
          </button>
          <button
            onClick={handleReset}
            className="p-1 text-slate-300 hover:text-white hover:bg-slate-700 rounded transition-colors"
            title="Reset View"
          >
            <RotateCcw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Main Canvas Viewport */}
      <div
        ref={containerRef}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
        className="relative w-full h-[460px] flex items-center justify-center overflow-hidden cursor-grab active:cursor-grabbing bg-black"
      >
        <div
          style={{
            transform: `translate(${position.x}px, ${position.y}px) scale(${zoom})`,
            transition: isDragging ? 'none' : 'transform 0.15s ease-out',
          }}
          className="relative w-[440px] h-[440px] flex items-center justify-center"
        >
          {/* Base Fundus Image */}
          <img
            src={activeImage}
            alt="Retinal Fundus"
            className="w-full h-full object-contain rounded-full shadow-2xl pointer-events-none"
          />

          {/* Grad-CAM Attention Heatmap Simulation Overlay */}
          {showHeatmap && (
            <div
              style={{ opacity: gradcamOpacity }}
              className="absolute inset-0 rounded-full pointer-events-none mix-blend-screen bg-gradient-radial from-amber-500/80 via-rose-600/50 to-transparent"
            />
          )}

          {/* Structure Overlays: Optic Disc & Fovea Center */}
          {showStructures && structures && (
            <svg className="absolute inset-0 w-full h-full pointer-events-none">
              {structures.opticDiscDetected && (
                <g>
                  <circle
                    cx={`${structures.opticDiscCenter[0] * 100}%`}
                    cy={`${structures.opticDiscCenter[1] * 100}%`}
                    r={`${structures.opticDiscRadius * 100}%`}
                    fill="rgba(59, 130, 246, 0.15)"
                    stroke="#3B82F6"
                    strokeWidth="2"
                    strokeDasharray="4 2"
                  />
                  <text
                    x={`${structures.opticDiscCenter[0] * 100}%`}
                    y={`${structures.opticDiscCenter[1] * 100 - 10}%`}
                    fill="#93C5FD"
                    fontSize="11"
                    fontWeight="bold"
                    textAnchor="middle"
                  >
                    Optic Disc
                  </text>
                </g>
              )}

              {structures.foveaDetected && (
                <g>
                  <circle
                    cx={`${structures.foveaCenter[0] * 100}%`}
                    cy={`${structures.foveaCenter[1] * 100}%`}
                    r={`${structures.foveaRadius * 100}%`}
                    fill="rgba(168, 85, 247, 0.2)"
                    stroke="#A855F7"
                    strokeWidth="2"
                  />
                  <text
                    x={`${structures.foveaCenter[0] * 100}%`}
                    y={`${structures.foveaCenter[1] * 100 + 15}%`}
                    fill="#D8B4FE"
                    fontSize="11"
                    fontWeight="bold"
                    textAnchor="middle"
                  >
                    Fovea Center
                  </text>
                </g>
              )}
            </svg>
          )}

          {/* Lesion Overlays */}
          {showLesions &&
            lesions.map((lesion) => {
              const [xMin, yMin, xMax, yMax] = lesion.boundingBox;
              const isSelected = highlightLesionId === lesion.id;
              const colorMap: Record<string, { border: string; bg: string; text: string }> = {
                microaneurysm: { border: '#EF4444', bg: 'rgba(239, 68, 68, 0.2)', text: '#FCA5A5' },
                hard_exudate: { border: '#EAB308', bg: 'rgba(234, 179, 8, 0.2)', text: '#FDE047' },
                soft_exudate: { border: '#F8FAFC', bg: 'rgba(248, 250, 252, 0.3)', text: '#FFFFFF' },
                hemorrhage: { border: '#DC2626', bg: 'rgba(220, 38, 38, 0.25)', text: '#F87171' },
                neovascularization: { border: '#9333EA', bg: 'rgba(147, 51, 234, 0.25)', text: '#C084FC' },
              };
              const style = colorMap[lesion.lesionType] || colorMap.microaneurysm;

              return (
                <div
                  key={lesion.id}
                  onClick={(e) => {
                    e.stopPropagation();
                    onSelectLesion?.(lesion);
                  }}
                  style={{
                    left: `${xMin * 100}%`,
                    top: `${yMin * 100}%`,
                    width: `${Math.max((xMax - xMin) * 100, 4)}%`,
                    height: `${Math.max((yMax - yMin) * 100, 4)}%`,
                    borderColor: style.border,
                    backgroundColor: style.bg,
                  }}
                  className={`absolute border-2 rounded-sm cursor-pointer transition-all hover:scale-110 group ${
                    isSelected ? 'ring-2 ring-white shadow-lg z-20' : 'z-10'
                  }`}
                >
                  <div
                    style={{ backgroundColor: style.border, color: '#FFFFFF' }}
                    className="opacity-0 group-hover:opacity-100 absolute -top-6 left-0 text-[10px] font-mono px-1.5 py-0.5 rounded shadow whitespace-nowrap pointer-events-none transition-opacity font-semibold"
                  >
                    {lesion.lesionType} ({(lesion.confidence * 100).toFixed(0)}%)
                  </div>
                </div>
              );
            })}
        </div>

        {/* Viewport Overlay Info */}
        <div className="absolute bottom-3 left-4 text-[11px] text-slate-400 bg-navy-900/80 px-2.5 py-1 rounded-md border border-slate-800 backdrop-blur-sm pointer-events-none">
          Click & drag to pan • Scroll to inspect microvasculature
        </div>
      </div>
    </div>
  );
};
