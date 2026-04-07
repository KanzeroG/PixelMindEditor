'use client';

import { useState } from 'react';
import { useEditorStore } from '@/store/editorStore';
import { getToolById } from '@/lib/tools';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Sparkles,
  Download,
  RotateCcw,
  Coins,
  ChevronDown,
  Play,
} from 'lucide-react';
import SponsoredPalette from '@/components/ads/SponsoredPalette';
import VideoAdModal from '@/components/ads/VideoAdModal';
import toast from 'react-hot-toast';
import { getApiBase, loginUser, runAITool } from '@/lib/api';
const TOKEN_STORAGE_KEY = 'pixelmind_token';

function dataUrlToFile(dataUrl: string, filename: string): File {
  const parts = dataUrl.split(',');
  if (parts.length !== 2) {
    throw new Error('Invalid image data URL');
  }
  const match = parts[0].match(/data:(.*?);base64/);
  const mime = match?.[1] || 'image/png';
  const binary = atob(parts[1]);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i += 1) {
    bytes[i] = binary.charCodeAt(i);
  }
  return new File([bytes], filename, { type: mime });
}

function createFallbackGeneratedImage(prompt: string): string {
  const canvas = document.createElement('canvas');
  canvas.width = 512;
  canvas.height = 512;
  const ctx = canvas.getContext('2d');
  if (!ctx) {
    throw new Error('Cannot create fallback image canvas');
  }
  const gradient = ctx.createLinearGradient(0, 0, 512, 512);
  gradient.addColorStop(0, '#8B5CF6');
  gradient.addColorStop(0.5, '#6D28D9');
  gradient.addColorStop(1, '#4C1D95');
  ctx.fillStyle = gradient;
  ctx.fillRect(0, 0, 512, 512);
  ctx.fillStyle = 'rgba(255,255,255,0.1)';
  ctx.font = '16px sans-serif';
  ctx.textAlign = 'center';
  ctx.fillText('AI Generated Result', 256, 240);
  ctx.fillText(`"${prompt.slice(0, 40)}"`, 256, 270);
  return canvas.toDataURL();
}

async function getTokenForAI(): Promise<string> {
  const cached = localStorage.getItem(TOKEN_STORAGE_KEY);
  if (cached) {
    return cached;
  }

  const login = await loginUser('demo@pixelmind.ai', 'demo1234');
  localStorage.setItem(TOKEN_STORAGE_KEY, login.access_token);
  return login.access_token;
}

export default function AISettingsPanel() {
  const selectedTool = useEditorStore((s) => s.selectedTool);
  const settings = useEditorStore((s) => s.settings);
  const updateSettings = useEditorStore((s) => s.updateSettings);
  const isProcessing = useEditorStore((s) => s.isProcessing);
  const setIsProcessing = useEditorStore((s) => s.setIsProcessing);
  const credits = useEditorStore((s) => s.credits);
  const setCredits = useEditorStore((s) => s.setCredits);
  const originalImage = useEditorStore((s) => s.originalImage);
  const originalFile = useEditorStore((s) => s.originalFile);
  const resultImage = useEditorStore((s) => s.resultImage);
  const setResultImage = useEditorStore((s) => s.setResultImage);
  const resetEditor = useEditorStore((s) => s.resetEditor);

  const [showAdModal, setShowAdModal] = useState(false);
  const [showAdvanced, setShowAdvanced] = useState(false);

  const tool = getToolById(selectedTool);
  if (!tool) return null;

  const canProcess =
    (!tool.requiresImage || originalImage) &&
    (!tool.requiresPrompt || settings.prompt.trim()) &&
    credits >= tool.creditCost &&
    !isProcessing;

  const handleGenerate = async () => {
    if (credits < tool.creditCost) {
      setShowAdModal(true);
      return;
    }

    setIsProcessing(true);
    let nextCredits = credits - tool.creditCost;

    try {
      if (selectedTool === 'remove-bg' && originalImage) {
        toast.success("Starting background removal...", { id: "bg-remove-toast" });
        const { removeBackground } = await import('@imgly/background-removal');
        
        const progressToastId = toast.loading("Downloading AI models (this takes a moment first time)...");
        
        const blob = await removeBackground(originalImage, {
          progress: (key, current, total) => {
            const pct = Math.round((current / total) * 100);
            if (pct % 25 === 0) { // update less frequently
              toast.loading(`Processing ${key}: ${pct}%`, { id: progressToastId });
            }
          }
        });
        
        const url = URL.createObjectURL(blob);
        setResultImage(url);
        toast.dismiss(progressToastId);
        toast.dismiss("bg-remove-toast");
      } else if (selectedTool === 'replace-bg' && settings.prompt && originalImage) {
        const progressToastId = toast.loading('Generating with PixelMind backend...');

        const imageFile = originalFile ?? dataUrlToFile(originalImage, `replace-bg-${Date.now()}.png`);
        const formData = new FormData();
        formData.append('image', imageFile);
        formData.append('prompt', settings.prompt);
        formData.append('strength', settings.strength.toString());
        formData.append('seed', settings.seed.toString());

        const token = await getTokenForAI();
        const result = await runAITool('replace-bg', formData, token);
        const absoluteResultUrl = result.result_url.startsWith('http')
          ? result.result_url
          : `${getApiBase()}${result.result_url}`;

        setResultImage(absoluteResultUrl);
        if (typeof result.remaining_credits === 'number') {
          nextCredits = result.remaining_credits;
        }
        toast.dismiss(progressToastId);
      } else if (['text-to-image', 'product-photo'].includes(selectedTool) && settings.prompt) {
        const progressToastId = toast.loading("Generating image with AI...");
        const promptParams = new URLSearchParams({
          seed: settings.seed.toString(),
          width: '512',
          height: '512',
          nologo: 'true'
        });
        
        let finalPrompt = settings.prompt;
        if (selectedTool === 'product-photo') {
           finalPrompt = `Professional product photography, studio lighting, highly detailed: ${settings.prompt}`;
        }
        
        const response = await fetch(`https://image.pollinations.ai/prompt/${encodeURIComponent(finalPrompt)}?${promptParams.toString()}`);
        if (response.ok) {
          const blob = await response.blob();
          const url = URL.createObjectURL(blob);
          setResultImage(url);
        } else {
          setResultImage(createFallbackGeneratedImage(settings.prompt));
          toast.error('External generator unavailable, using local fallback output.');
        }
        toast.dismiss(progressToastId);
      } else {
        // Simulate processing (mock) for other tools
        const duration = tool.creditCost === 2 ? 4000 : 2500;
        await new Promise((r) => setTimeout(r, duration));

        // Mock result: use original image or a gradient placeholder
        if (originalImage && selectedTool !== 'text-to-image') {
          setResultImage(originalImage);
        } else {
          setResultImage(createFallbackGeneratedImage(settings.prompt));
        }
      }

      setCredits(nextCredits);
      toast.success(`${tool.name} complete! -${tool.creditCost} credit${tool.creditCost > 1 ? 's' : ''}`);
    } catch (error) {
      console.error("AI Generation Error:", error);
      toast.error("Failed to process image");
      toast.dismiss();
    } finally {
      setIsProcessing(false);
    }
  };

  const handleDownload = () => {
    if (!resultImage) return;
    const a = document.createElement('a');
    a.href = resultImage;
    a.download = `pixelmind-${selectedTool}-${Date.now()}.png`;
    a.click();
    toast.success('Image downloaded!');
  };

  return (
    <>
      <aside className="w-80 bg-onyx-surface border-l border-slate-dim/30 flex flex-col z-30 overflow-hidden">
        {/* Header */}
        <div className="px-5 py-4 border-b border-slate-dim/30">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-violet-ghost flex items-center justify-center">
              <Sparkles className="w-4 h-4 text-electric-violet" />
            </div>
            <div>
              <h2 className="text-white-primary font-semibold text-sm">{tool.name}</h2>
              <p className="text-slate-muted text-xs">{tool.creditCost} credit{tool.creditCost > 1 ? 's' : ''} per use</p>
            </div>
          </div>
        </div>

        {/* Settings */}
        <div className="flex-1 overflow-y-auto p-5 space-y-5">
          {/* Prompt */}
          {tool.requiresPrompt && (
            <div>
              <label className="block text-xs text-slate-primary font-medium uppercase tracking-wider mb-2">
                Prompt
              </label>
              <textarea
                value={settings.prompt}
                onChange={(e) => updateSettings({ prompt: e.target.value })}
                placeholder={
                  selectedTool === 'text-to-image'
                    ? 'A serene mountain landscape at golden hour, cinematic lighting...'
                    : selectedTool === 'replace-bg'
                    ? 'A modern office with large windows and city view...'
                    : 'Describe what you want...'
                }
                rows={4}
                className="w-full px-3.5 py-3 rounded-xl bg-onyx-elevated border border-slate-dim/50 text-white-primary text-sm placeholder:text-slate-dim/80 focus:outline-none focus:border-electric-violet focus:ring-1 focus:ring-electric-violet/30 transition-all resize-none"
                id="ai-prompt-input"
              />
            </div>
          )}

          {/* Strength Slider */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="text-xs text-slate-primary font-medium uppercase tracking-wider">
                Strength
              </label>
              <span className="text-xs text-slate-muted font-mono">
                {settings.strength.toFixed(2)}
              </span>
            </div>
            <input
              type="range"
              min={0}
              max={1}
              step={0.05}
              value={settings.strength}
              onChange={(e) => updateSettings({ strength: parseFloat(e.target.value) })}
              className="w-full h-1.5 rounded-full appearance-none bg-slate-dim/50 accent-electric-violet cursor-pointer"
              id="ai-strength-slider"
            />
            <div className="flex justify-between mt-1">
              <span className="text-[10px] text-slate-dim">Subtle</span>
              <span className="text-[10px] text-slate-dim">Strong</span>
            </div>
          </div>

          {/* Advanced Settings */}
          <div>
            <button
              onClick={() => setShowAdvanced(!showAdvanced)}
              className="flex items-center gap-2 text-xs text-slate-muted hover:text-slate-primary transition-colors w-full"
            >
              <ChevronDown
                className={`w-3.5 h-3.5 transition-transform ${showAdvanced ? 'rotate-180' : ''}`}
              />
              Advanced Settings
            </button>

            <AnimatePresence>
              {showAdvanced && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: 'auto', opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  transition={{ duration: 0.2 }}
                  className="overflow-hidden"
                >
                  <div className="pt-3 space-y-4">
                    {/* Seed */}
                    <div>
                      <label className="block text-xs text-slate-primary font-medium uppercase tracking-wider mb-2">
                        Seed
                      </label>
                      <div className="flex gap-2">
                        <input
                          type="number"
                          value={settings.seed}
                          onChange={(e) => updateSettings({ seed: parseInt(e.target.value) || 0 })}
                          className="flex-1 px-3 py-2 rounded-lg bg-onyx-elevated border border-slate-dim/50 text-white-primary text-sm font-mono focus:outline-none focus:border-electric-violet transition-all"
                          id="ai-seed-input"
                        />
                        <button
                          onClick={() => updateSettings({ seed: Math.floor(Math.random() * 99999) })}
                          className="px-3 py-2 rounded-lg bg-onyx-elevated border border-slate-dim/50 text-slate-muted hover:text-white-primary hover:border-electric-violet transition-all text-xs"
                        >
                          🎲
                        </button>
                      </div>
                    </div>

                    {/* Brush Size (for mask tools) */}
                    {tool.requiresMask && (
                      <div>
                        <div className="flex items-center justify-between mb-2">
                          <label className="text-xs text-slate-primary font-medium uppercase tracking-wider">
                            Brush Size
                          </label>
                          <span className="text-xs text-slate-muted font-mono">
                            {settings.brushSize}px
                          </span>
                        </div>
                        <input
                          type="range"
                          min={5}
                          max={100}
                          step={1}
                          value={settings.brushSize}
                          onChange={(e) => updateSettings({ brushSize: parseInt(e.target.value) })}
                          className="w-full h-1.5 rounded-full appearance-none bg-slate-dim/50 accent-electric-violet cursor-pointer"
                        />
                      </div>
                    )}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          {/* Tool Description */}
          <div className="p-3.5 rounded-xl bg-onyx-elevated/50 border border-slate-dim/20">
            <p className="text-xs text-slate-muted leading-relaxed">{tool.description}</p>
          </div>

          {/* Sponsored Palette (shown during processing) */}
          <AnimatePresence>
            {isProcessing && <SponsoredPalette />}
          </AnimatePresence>
        </div>

        {/* Bottom Actions */}
        <div className="p-5 border-t border-slate-dim/30 space-y-3">
          {/* Credit Display */}
          <div className="flex items-center justify-between px-3 py-2.5 rounded-xl bg-onyx-elevated">
            <div className="flex items-center gap-2">
              <Coins className="w-4 h-4 text-warning" />
              <span className="text-sm text-white-primary font-medium">{credits} credits</span>
            </div>
            {credits <= 3 && (
              <button
                onClick={() => setShowAdModal(true)}
                className="text-xs text-electric-violet hover:text-violet-glow font-medium transition-colors"
              >
                + Refill
              </button>
            )}
          </div>

          {/* Generate Button */}
          <button
            onClick={handleGenerate}
            disabled={!canProcess}
            className={`w-full flex items-center justify-center gap-2 py-3.5 rounded-xl font-semibold transition-all ${
              canProcess
                ? 'bg-gradient-to-r from-electric-violet to-violet-dim text-white hover:shadow-[0_8px_32px_rgba(139,92,246,0.3)] hover:-translate-y-px'
                : 'bg-onyx-elevated text-slate-dim cursor-not-allowed'
            }`}
            id="ai-generate-btn"
          >
            {isProcessing ? (
              <>
                <div className="w-4 h-4 border-2 border-white/20 border-t-white rounded-full animate-spin" />
                Processing...
              </>
            ) : credits < tool.creditCost ? (
              <>
                <Coins className="w-4 h-4" />
                Need {tool.creditCost} Credits
              </>
            ) : (
              <>
                <Play className="w-4 h-4" />
                Generate — {tool.creditCost}cr
              </>
            )}
          </button>

          {/* Download + Reset (when result exists) */}
          {resultImage && (
            <div className="flex gap-2">
              <button
                onClick={handleDownload}
                className="flex-1 flex items-center justify-center gap-2 py-2.5 rounded-xl border border-slate-dim/50 text-slate-primary text-sm font-medium hover:border-electric-violet hover:text-violet-glow hover:bg-violet-ghost transition-all"
                id="download-btn"
              >
                <Download className="w-4 h-4" />
                Download
              </button>
              <button
                onClick={resetEditor}
                className="flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl border border-slate-dim/50 text-slate-muted hover:text-white-primary hover:border-slate-muted transition-all"
                title="New image"
              >
                <RotateCcw className="w-4 h-4" />
              </button>
            </div>
          )}
        </div>
      </aside>

      {/* Video Ad Modal */}
      <VideoAdModal isOpen={showAdModal} onClose={() => setShowAdModal(false)} />
    </>
  );
}
