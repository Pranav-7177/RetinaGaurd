import React, { useState, useRef } from 'react';
import {
  Upload,
  ArrowRight,
  FileImage,
  Sparkles,
  CheckCircle2,
  AlertCircle,
  Trash2,
  RefreshCw,
  Maximize2,
  ZoomIn,
  ZoomOut,
  RotateCcw,
  Info,
  X,
  Eye
} from 'lucide-react';
import { Button } from '../common/Button';
import { Card } from '../common/Card';
import { Modal } from '../common/Modal';
import { EyeSide, ImageMetadata } from '../../types';
import { PatientFormData } from './PatientStep';

interface ImageUploadProps {
  patientData: PatientFormData;
  imageUrl?: string;
  imageMetadata?: ImageMetadata;
  onUpdatePatientData?: (data: Partial<PatientFormData>) => void;
  onImageSelected: (url: string, metadata: ImageMetadata, file?: File | Blob) => void;
  onRemoveImage: () => void;
  onNext: () => void;
  onBack: () => void;
  isAnalyzing?: boolean;
  analysisError?: string | null;
}

const PRESET_SAMPLES = [
  {
    id: 'dr2',
    name: 'Sample A: Moderate NPDR (Grade 2)',
    url: '/assets/samples/sample_dr2_fundus.png',
    fileName: 'sample_moderate_npdr_od.png',
    fileSize: '1.9 MB',
    dimensions: '2048 × 1536 px',
    desc: 'Microaneurysms and lipid exudates present in temporal region',
    tag: 'Referable DR (Grade 2)'
  },
  {
    id: 'normal',
    name: 'Sample B: Normal Healthy Fundus (Grade 0)',
    url: '/assets/samples/sample_normal_fundus.png',
    fileName: 'sample_normal_healthy_os.png',
    fileSize: '0.9 MB',
    dimensions: '2048 × 1536 px',
    desc: 'Clear macular background and sharp optic disc margins',
    tag: 'Non-Referable (Grade 0)'
  },
  {
    id: 'dr3',
    name: 'Sample C: Severe NPDR (Grade 3)',
    url: '/assets/samples/sample_dr3_fundus.png',
    fileName: 'sample_severe_npdr_421.png',
    fileSize: '1.6 MB',
    dimensions: '2560 × 1920 px',
    desc: 'Extensive blot hemorrhages and cotton wool spots',
    tag: 'Urgent Referable (Grade 3)'
  },
  {
    id: 'ungradable',
    name: 'Sample D: Ungradable Low Quality Capture',
    url: '/assets/samples/sample_ungradable.png',
    fileName: 'sample_ungradable_blur.png',
    fileSize: '1.1 MB',
    dimensions: '1920 × 1440 px',
    desc: 'Severe motion blur & flash illumination defect',
    tag: 'Ungradable (Recapture)'
  },
];

const MAX_FILE_SIZE_BYTES = 25 * 1024 * 1024; // 25 MB
const ALLOWED_TYPES = ['image/jpeg', 'image/jpg', 'image/png', 'image/svg+xml'];

export const ImageUpload: React.FC<ImageUploadProps> = ({
  patientData,
  imageUrl,
  imageMetadata,
  onUpdatePatientData,
  onImageSelected,
  onRemoveImage,
  onNext,
  onBack,
  isAnalyzing = false,
  analysisError = null,
}) => {
  const [dragActive, setDragActive] = useState(false);
  const [validationError, setValidationError] = useState<string | null>(null);
  const [isFullscreen, setIsFullscreen] = useState(false);

  // Local interactive zoom state for preview
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });

  const fileInputRef = useRef<HTMLInputElement>(null);

  const processFile = (file: File) => {
    setValidationError(null);

    // Validate type
    if (!ALLOWED_TYPES.includes(file.type.toLowerCase()) && !file.name.match(/\.(jpg|jpeg|png|svg)$/i)) {
      setValidationError('Invalid file format. Please upload a JPG, JPEG, or PNG fundus photograph.');
      return;
    }

    // Validate size
    if (file.size > MAX_FILE_SIZE_BYTES) {
      setValidationError(`File size exceeds 25MB limit (${(file.size / (1024 * 1024)).toFixed(1)}MB). Please upload a compressed capture.`);
      return;
    }

    const localUrl = URL.createObjectURL(file);
    const img = new Image();
    img.onload = () => {
      const dimensions = `${img.naturalWidth} × ${img.naturalHeight} px`;
      const sizeMB = (file.size / (1024 * 1024)).toFixed(2) + ' MB';
      const ext = file.name.split('.').pop()?.toUpperCase() || 'JPG';

      const meta: ImageMetadata = {
        fileName: file.name,
        fileSizeFormatted: sizeMB,
        sizeBytes: file.size,
        dimensions,
        fileFormat: ext,
        uploadedAt: new Date().toLocaleTimeString(),
      };
      onImageSelected(localUrl, meta, file);
      setZoom(1);
      setPan({ x: 0, y: 0 });
    };
    img.src = localUrl;
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      processFile(e.target.files[0]);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      processFile(e.dataTransfer.files[0]);
    }
  };

  const handleSelectPreset = async (sample: typeof PRESET_SAMPLES[0]) => {
    setValidationError(null);
    const meta: ImageMetadata = {
      fileName: sample.fileName,
      fileSizeFormatted: sample.fileSize,
      sizeBytes: 2 * 1024 * 1024,
      dimensions: sample.dimensions,
      fileFormat: 'PNG',
      uploadedAt: new Date().toLocaleTimeString(),
    };
    try {
      const resp = await fetch(sample.url);
      const blob = await resp.blob();
      const fileObj = new File([blob], sample.fileName, { type: 'image/png' });
      onImageSelected(sample.url, meta, fileObj);
    } catch {
      onImageSelected(sample.url, meta);
    }
    setZoom(1);
    setPan({ x: 0, y: 0 });
  };

  const handleSaveAndAnalyze = () => {
    if (isAnalyzing) return;
    if (!imageUrl) {
      setValidationError('Please upload a fundus image to proceed.');
      return;
    }
    onNext();
  };

  // Zoom helpers
  const handleZoomIn = () => setZoom((z) => Math.min(z + 0.25, 3.5));
  const handleZoomOut = () => setZoom((z) => Math.max(z - 0.25, 0.75));
  const handleResetZoom = () => {
    setZoom(1);
    setPan({ x: 0, y: 0 });
  };
  const handleFitToView = () => {
    setZoom(1);
    setPan({ x: 0, y: 0 });
  };

  const handleMouseDown = (e: React.MouseEvent) => {
    if (zoom > 1) {
      setIsDragging(true);
      setDragStart({ x: e.clientX - pan.x, y: e.clientY - pan.y });
    }
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (isDragging) {
      setPan({ x: e.clientX - dragStart.x, y: e.clientY - dragStart.y });
    }
  };

  const handleMouseUp = () => setIsDragging(false);

  const eyeDisplayLabel =
    patientData.eye === 'OD'
      ? 'Right Eye (OD)'
      : patientData.eye === 'OS'
      ? 'Left Eye (OS)'
      : 'Not Specified';

  return (
    <div className="space-y-6">
      {/* Step Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-navy-950">Step 2 — Single Fundus Image Upload</h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Upload one fundus image for this screening. Eye side is optional and defaults to Not Specified ({eyeDisplayLabel}).
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={onBack}>
            Back
          </Button>
          <Button
            variant="teal"
            size="sm"
            onClick={handleSaveAndAnalyze}
            disabled={isAnalyzing}
            rightIcon={isAnalyzing ? <RefreshCw className="w-4 h-4 animate-spin" /> : <ArrowRight className="w-4 h-4" />}
          >
            {isAnalyzing ? 'Analyzing Image...' : 'Save & Analyze'}
          </Button>
        </div>
      </div>

      {analysisError && (
        <div className="p-4 bg-amber-50 border border-amber-200 rounded-2xl flex items-start gap-3 text-amber-900">
          <AlertCircle className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
          <div className="text-xs">
            <span className="font-bold">Screening Notice: </span>
            {analysisError}
          </div>
        </div>
      )}

      {/* Eye Side (Optional) Selector Strip */}
      <div className="p-4 bg-white border border-slate-200 rounded-2xl shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <Eye className="w-4 h-4 text-teal-600" />
            <span className="text-xs font-bold text-navy-950">Examined Eye Side (Optional)</span>
            <span className="text-[10px] font-semibold px-2 py-0.5 rounded bg-slate-100 text-slate-600">
              Default: Not Specified
            </span>
          </div>
          <p className="text-[11px] text-slate-500 mt-1">
            One screening = one fundus image. If evaluating both eyes, conduct two separate screenings.
          </p>
        </div>
        <div className="grid grid-cols-3 gap-2 w-full sm:w-auto">
          {[
            { id: 'OS' as EyeSide, label: 'Left Eye (OS)' },
            { id: 'OD' as EyeSide, label: 'Right Eye (OD)' },
            { id: 'NOT_SPECIFIED' as EyeSide, label: 'Not Specified' },
          ].map((opt) => {
            const isSelected = (patientData.eye || 'NOT_SPECIFIED') === opt.id;
            return (
              <button
                key={opt.id}
                type="button"
                onClick={() => onUpdatePatientData?.({ eye: opt.id })}
                className={`py-2 px-3 rounded-xl border text-xs font-bold transition-all text-center ${
                  isSelected
                    ? 'bg-navy-900 border-navy-900 text-white shadow-sm'
                    : 'bg-slate-50 border-slate-200 text-slate-700 hover:bg-slate-100'
                }`}
              >
                {opt.label}
              </button>
            );
          })}
        </div>
      </div>

      {validationError && (
        <div className="p-3 bg-rose-50 border border-rose-200 rounded-xl text-xs text-rose-800 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-rose-600 flex-shrink-0" />
            <span>{validationError}</span>
          </div>
          <button onClick={() => setValidationError(null)} className="text-rose-400 hover:text-rose-600">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {!imageUrl && (
        <div className="p-3 bg-amber-50 border border-amber-200 rounded-xl text-xs text-amber-800 flex items-center gap-2">
          <AlertCircle className="w-4 h-4 text-amber-600 flex-shrink-0" />
          <span>Please upload a fundus image to proceed.</span>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Upload Target & Preview Viewer (7 cols) */}
        <div className="lg:col-span-7 space-y-4">
          <Card title="Fundus Photograph Acquisition">
            {imageUrl ? (
              <div className="space-y-4">
                {/* Image Toolbar */}
                <div className="flex items-center justify-between bg-slate-900 text-slate-200 px-4 py-2.5 rounded-t-xl text-xs">
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-teal-400 font-mono">
                      Original Fundus Photograph ({eyeDisplayLabel})
                    </span>
                    <span className="text-[11px] text-slate-400 font-mono">
                      Zoom: {Math.round(zoom * 100)}%
                    </span>
                  </div>

                  <div className="flex items-center gap-1">
                    <button
                      type="button"
                      onClick={handleZoomIn}
                      className="p-1 rounded hover:bg-slate-800 text-slate-300 hover:text-white"
                      title="Zoom In"
                    >
                      <ZoomIn className="w-4 h-4" />
                    </button>
                    <button
                      type="button"
                      onClick={handleZoomOut}
                      className="p-1 rounded hover:bg-slate-800 text-slate-300 hover:text-white"
                      title="Zoom Out"
                    >
                      <ZoomOut className="w-4 h-4" />
                    </button>
                    <button
                      type="button"
                      onClick={handleFitToView}
                      className="px-2 py-0.5 rounded text-[10px] font-medium bg-slate-800 hover:bg-slate-700 text-slate-300"
                      title="Fit to View"
                    >
                      Fit
                    </button>
                    <button
                      type="button"
                      onClick={handleResetZoom}
                      className="p-1 rounded hover:bg-slate-800 text-slate-300 hover:text-white"
                      title="Reset Zoom"
                    >
                      <RotateCcw className="w-3.5 h-3.5" />
                    </button>
                    <button
                      type="button"
                      onClick={() => setIsFullscreen(true)}
                      className="p-1 rounded hover:bg-slate-800 text-slate-300 hover:text-white"
                      title="Fullscreen Viewer"
                    >
                      <Maximize2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>

                {/* Viewport Box */}
                <div
                  onMouseDown={handleMouseDown}
                  onMouseMove={handleMouseMove}
                  onMouseUp={handleMouseUp}
                  onMouseLeave={handleMouseUp}
                  className={`w-full h-80 bg-black rounded-b-xl overflow-hidden relative flex items-center justify-center select-none ${
                    zoom > 1 ? 'cursor-grab active:cursor-grabbing' : ''
                  }`}
                >
                  <div
                    style={{
                      transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})`,
                      transition: isDragging ? 'none' : 'transform 0.15s ease-out',
                    }}
                    className="w-72 h-72 rounded-full overflow-hidden flex items-center justify-center bg-black"
                  >
                    <img src={imageUrl} alt="Fundus Capture" className="w-full h-full object-contain pointer-events-none" />
                  </div>

                  <span className="absolute bottom-2 right-3 text-[10px] text-slate-400 font-mono bg-slate-900/80 px-2 py-0.5 rounded backdrop-blur-sm">
                    {imageMetadata?.dimensions || '2048 × 1536 px'}
                  </span>
                </div>

                {/* Image Metadata Strip */}
                {imageMetadata && (
                  <div className="p-3 bg-slate-50 rounded-xl border border-slate-200 grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
                    <div>
                      <span className="text-slate-400 text-[10px] uppercase font-semibold">File Name</span>
                      <div className="font-bold text-navy-950 truncate">{imageMetadata.fileName}</div>
                    </div>
                    <div>
                      <span className="text-slate-400 text-[10px] uppercase font-semibold">Format</span>
                      <div className="font-bold text-slate-800">{imageMetadata.fileFormat}</div>
                    </div>
                    <div>
                      <span className="text-slate-400 text-[10px] uppercase font-semibold">File Size</span>
                      <div className="font-bold text-slate-800">{imageMetadata.fileSizeFormatted}</div>
                    </div>
                    <div>
                      <span className="text-slate-400 text-[10px] uppercase font-semibold">Resolution</span>
                      <div className="font-bold text-teal-700">{imageMetadata.dimensions}</div>
                    </div>
                  </div>
                )}

                {/* Actions: Replace / Remove */}
                <div className="flex items-center justify-between pt-2">
                  <button
                    type="button"
                    onClick={onRemoveImage}
                    className="text-xs text-rose-600 hover:text-rose-700 font-semibold inline-flex items-center gap-1.5"
                  >
                    <Trash2 className="w-3.5 h-3.5" /> Remove Image
                  </button>

                  <button
                    type="button"
                    onClick={() => fileInputRef.current?.click()}
                    className="text-xs text-teal-700 hover:text-teal-800 font-semibold inline-flex items-center gap-1.5"
                  >
                    <RefreshCw className="w-3.5 h-3.5" /> Replace with Local File
                  </button>
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept=".jpg,.jpeg,.png,.svg"
                    onChange={handleFileChange}
                    className="hidden"
                  />
                </div>
              </div>
            ) : (
              /* Dropzone */
              <div
                onDragOver={(e) => { e.preventDefault(); setDragActive(true); }}
                onDragLeave={() => setDragActive(false)}
                onDrop={handleDrop}
                className={`border-2 border-dashed rounded-2xl p-10 text-center transition-all ${
                  dragActive
                    ? 'border-teal-500 bg-teal-50/50'
                    : 'border-slate-300 bg-slate-50 hover:bg-slate-100/60'
                }`}
              >
                <div className="space-y-4">
                  <div className="w-14 h-14 mx-auto rounded-2xl bg-teal-100 text-teal-700 flex items-center justify-center">
                    <Upload className="w-7 h-7" />
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-navy-950">
                      Drag and drop single fundus camera photograph here
                    </p>
                    <p className="text-xs text-slate-500 mt-1">
                      Supports high-resolution JPG, JPEG, and PNG captures (one image per screening, max 25MB)
                    </p>
                  </div>
                  <label className="inline-block cursor-pointer">
                    <span className="px-4 py-2 bg-navy-900 text-white rounded-lg text-xs font-semibold hover:bg-navy-800 shadow-sm inline-flex items-center gap-2">
                      <FileImage className="w-4 h-4" /> Browse Local Files
                    </span>
                    <input
                      ref={fileInputRef}
                      type="file"
                      accept=".jpg,.jpeg,.png,.svg"
                      onChange={handleFileChange}
                      className="hidden"
                    />
                  </label>
                </div>
              </div>
            )}
          </Card>
        </div>

        {/* Right Column: Preloaded Calibrated Test Library (5 cols) */}
        <div className="lg:col-span-5 space-y-4">
          <Card
            title="Preloaded Calibrated Sample Library"
            subtitle="Demonstration fundus sets with varied diabetic retinopathy severity stages"
          >
            <div className="space-y-2.5">
              {PRESET_SAMPLES.map((sample) => {
                const isSelected = imageUrl === sample.url;
                return (
                  <div
                    key={sample.id}
                    onClick={() => handleSelectPreset(sample)}
                    className={`p-3 rounded-xl border transition-all cursor-pointer flex items-center gap-3 ${
                      isSelected
                        ? 'bg-teal-50 border-teal-500 ring-2 ring-teal-400/30'
                        : 'bg-white border-slate-200 hover:border-slate-300 hover:bg-slate-50'
                    }`}
                  >
                    <div className="w-12 h-12 rounded-full overflow-hidden flex-shrink-0 bg-black border border-slate-300">
                      <img src={sample.url} alt={sample.name} className="w-full h-full object-contain" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="text-xs font-bold text-navy-950 truncate">{sample.name}</div>
                      <div className="text-[11px] text-slate-500 mt-0.5">{sample.desc}</div>
                      <div className="flex items-center gap-2 mt-1">
                        <span className="text-[10px] font-semibold px-2 py-0.5 rounded bg-slate-100 text-slate-700">
                          {sample.tag}
                        </span>
                        <span className="text-[10px] text-slate-400 font-mono">{sample.dimensions}</span>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </Card>
        </div>
      </div>

      {/* Fullscreen Preview Modal */}
      {isFullscreen && imageUrl && (
        <Modal
          isOpen={true}
          onClose={() => setIsFullscreen(false)}
          title={`Fundus Photograph Inspection: ${patientData.name}`}
          subtitle={`Candidate ID: ${patientData.patientId} • Eye: ${eyeDisplayLabel} • File: ${imageMetadata?.fileName || 'fundus.jpg'}`}
          maxWidth="4xl"
        >
          <div className="w-full h-[520px] bg-black rounded-xl overflow-hidden flex items-center justify-center relative">
            <img src={imageUrl} alt="Fundus Fullscreen" className="max-w-full max-h-full object-contain" />
          </div>
        </Modal>
      )}
    </div>
  );
};
