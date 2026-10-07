import React, { useState } from 'react';
import { ArrowRight, AlertTriangle, Eye, Crosshair, Filter, ShieldCheck, CheckCircle2, Info } from 'lucide-react';
import { Button } from '../common/Button';
import { Card } from '../common/Card';
import { ImageZoomViewer } from '../common/ImageZoomViewer';
import { LesionFinding, RetinalStructure } from '../../types';

interface LesionMapProps {
  imageUrl: string;
  enhancedImageUrl?: string;
  structures?: RetinalStructure;
  lesions: LesionFinding[];
  onNext: () => void;
  onBack: () => void;
}

export const LesionMap: React.FC<LesionMapProps> = ({
  imageUrl,
  enhancedImageUrl,
  structures,
  lesions,
  onNext,
  onBack,
}) => {
  const [selectedLesionId, setSelectedLesionId] = useState<string | undefined>(lesions[0]?.id);
  const [filterType, setFilterType] = useState<string>('ALL');

  const filteredLesions = lesions.filter(
    (l) => filterType === 'ALL' || l.lesionType === filterType
  );

  // Category counts
  const microCount = lesions.filter((l) => l.lesionType === 'microaneurysm').length;
  const hemorrhageCount = lesions.filter((l) => l.lesionType === 'hemorrhage').length;
  const hardExudateCount = lesions.filter((l) => l.lesionType === 'hard_exudate').length;
  const softExudateCount = lesions.filter((l) => l.lesionType === 'soft_exudate').length;
  const neovascularCount = lesions.filter((l) => l.lesionType === 'neovascularization').length;

  return (
    <div className="space-y-6">
      {/* Step Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-xl font-bold text-navy-950">Step 6 — Candidate Lesion Findings</h2>
            <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-amber-100 text-amber-900 border border-amber-300">
              Demo / Candidate Detections
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-0.5">
            Automated screening localization of microvascular hallmarks (microaneurysms, hemorrhages, lipid exudates, and ischemic cotton wool spots).
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={onBack}>
            Back
          </Button>
          <Button variant="teal" size="sm" onClick={onNext} rightIcon={<ArrowRight className="w-4 h-4" />}>
            Proceed to DR Severity Classification
          </Button>
        </div>
      </div>

      {/* 5 Lesion Category Count Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
        <div className="p-3 bg-white rounded-xl border border-slate-200 shadow-card-subtle">
          <span className="text-[10px] font-bold uppercase text-slate-400">Microaneurysms</span>
          <div className="text-lg font-bold font-mono text-red-600 mt-0.5">{microCount} candidates</div>
          <div className="text-[10px] text-slate-500">Capillary outpouching</div>
        </div>

        <div className="p-3 bg-white rounded-xl border border-slate-200 shadow-card-subtle">
          <span className="text-[10px] font-bold uppercase text-slate-400">Hemorrhages</span>
          <div className="text-lg font-bold font-mono text-rose-700 mt-0.5">{hemorrhageCount} candidates</div>
          <div className="text-[10px] text-slate-500">Dot/blot/flame pools</div>
        </div>

        <div className="p-3 bg-white rounded-xl border border-slate-200 shadow-card-subtle">
          <span className="text-[10px] font-bold uppercase text-slate-400">Hard Exudates</span>
          <div className="text-lg font-bold font-mono text-amber-600 mt-0.5">{hardExudateCount} candidates</div>
          <div className="text-[10px] text-slate-500">Lipid precipitates</div>
        </div>

        <div className="p-3 bg-white rounded-xl border border-slate-200 shadow-card-subtle">
          <span className="text-[10px] font-bold uppercase text-slate-400">Soft Exudates</span>
          <div className="text-lg font-bold font-mono text-slate-700 mt-0.5">{softExudateCount} candidates</div>
          <div className="text-[10px] text-slate-500">Cotton wool spots</div>
        </div>

        <div className="p-3 bg-white rounded-xl border border-slate-200 shadow-card-subtle">
          <span className="text-[10px] font-bold uppercase text-slate-400">Neovascularization</span>
          <div className="text-lg font-bold font-mono text-purple-700 mt-0.5">{neovascularCount} candidates</div>
          <div className="text-[10px] text-slate-500">New vessel fronds</div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Interactive Image Viewport (7 cols) */}
        <div className="lg:col-span-7 space-y-4">
          <ImageZoomViewer
            imageUrl={imageUrl}
            enhancedImageUrl={enhancedImageUrl}
            structures={structures}
            lesions={filteredLesions}
            highlightLesionId={selectedLesionId}
            onSelectLesion={(l) => setSelectedLesionId(l.id)}
            title="Candidate Lesion Bounding Boxes"
          />
        </div>

        {/* Right Column: Candidate Evidence List (5 cols) */}
        <div className="lg:col-span-5 space-y-4">
          <Card
            title={`Candidate Findings (${filteredLesions.length})`}
            subtitle="Candidate regions identified for clinician review"
            headerAction={
              <select
                value={filterType}
                onChange={(e) => setFilterType(e.target.value)}
                className="text-xs rounded-lg border border-slate-200 py-1 px-2 focus:outline-none focus:ring-1 focus:ring-teal-500 text-slate-700 font-medium bg-slate-50"
              >
                <option value="ALL">All Categories ({lesions.length})</option>
                <option value="microaneurysm">Microaneurysms ({microCount})</option>
                <option value="hemorrhage">Hemorrhages ({hemorrhageCount})</option>
                <option value="hard_exudate">Hard Exudates ({hardExudateCount})</option>
                <option value="soft_exudate">Soft Exudates ({softExudateCount})</option>
                <option value="neovascularization">Neovascularization ({neovascularCount})</option>
              </select>
            }
          >
            {filteredLesions.length === 0 ? (
              <div className="text-center py-10 space-y-2">
                <CheckCircle2 className="w-8 h-8 text-emerald-500 mx-auto" />
                <div className="text-xs font-bold text-navy-950">No Candidate Lesions in this Category</div>
                <p className="text-[11px] text-slate-500 max-w-xs mx-auto">
                  Fundus inspection did not identify candidate findings for this lesion filter.
                </p>
              </div>
            ) : (
              <div className="space-y-2.5 max-h-[360px] overflow-y-auto pr-1">
                {filteredLesions.map((lesion) => {
                  const isSelected = selectedLesionId === lesion.id;
                  const tagColors: Record<string, { bg: string; text: string }> = {
                    microaneurysm: { bg: 'bg-red-50', text: 'text-red-700' },
                    hard_exudate: { bg: 'bg-amber-50', text: 'text-amber-700' },
                    soft_exudate: { bg: 'bg-slate-100', text: 'text-slate-800' },
                    hemorrhage: { bg: 'bg-rose-50', text: 'text-rose-700' },
                    neovascularization: { bg: 'bg-purple-50', text: 'text-purple-700' },
                  };
                  const color = tagColors[lesion.lesionType] || tagColors.microaneurysm;

                  return (
                    <div
                      key={lesion.id}
                      onClick={() => setSelectedLesionId(lesion.id)}
                      className={`p-3 rounded-xl border transition-all cursor-pointer text-xs ${
                        isSelected
                          ? 'bg-teal-50/70 border-teal-500 ring-2 ring-teal-400/30'
                          : 'bg-white border-slate-200 hover:border-slate-300 hover:bg-slate-50'
                      }`}
                    >
                      <div className="flex items-center justify-between mb-1">
                        <div className="flex items-center gap-2">
                          <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider ${color.bg} ${color.text}`}>
                            {lesion.lesionType.replace('_', ' ')}
                          </span>
                          <span className="font-mono text-slate-400 text-[10px]">{lesion.id}</span>
                        </div>
                        <span className="font-mono font-bold text-navy-950 text-xs">
                          Confidence: {(lesion.confidence * 100).toFixed(0)}%
                        </span>
                      </div>

                      <p className="text-[11px] text-slate-700 leading-snug">
                        {lesion.clinicalSignificance}
                      </p>

                      <div className="mt-1.5 flex items-center justify-between text-[10px] text-slate-500">
                        <span>Approximate Location: <span className="font-semibold text-slate-700">{lesion.approximateLocation || lesion.locationQuadrant.replace('_', ' ')}</span></span>
                        <span className="font-mono uppercase text-slate-400">{lesion.locationQuadrant.replace('_', ' ')}</span>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </Card>

          <div className="p-3 bg-slate-50 rounded-lg border border-slate-200 text-[11px] text-slate-500 flex items-start gap-2">
            <Info className="w-3.5 h-3.5 text-slate-400 mt-0.5 flex-shrink-0" />
            <span>
              Candidate findings indicate regions of interest generated by deep learning bounding box proposal networks. These do not represent confirmed clinical diagnoses until verified by the reviewing doctor.
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};
