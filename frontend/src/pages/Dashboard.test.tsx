import { render, screen, fireEvent } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import { Dashboard } from "../pages/Dashboard";
import { useSynthesis, useVoices } from "../hooks/useSynthesis";
import { vi, describe, beforeEach, test, expect } from "vitest";

vi.mock("../hooks/useSynthesis");
vi.mock("../api/client");

const mockVoices = [
  { id: 1, name: "Test Voice", description: "A test voice", voice_type: "builtin", language: "en", sample_rate: 22050, is_active: true, created_at: "", updated_at: "", owner_id: null, model_id: "test", reference_audio_path: null, design_params: null },
];

const mockJobs = [
  { id: 1, text: "Hello world", voice_id: 1, status: "completed", output_path: "/tmp/test.wav", duration_seconds: 5, error_message: null, speed: 100, pitch: 0, created_at: new Date().toISOString(), started_at: null, completed_at: null, owner_id: 1, voice: mockVoices[0] },
];

describe("Dashboard", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (useVoices as any).mockReturnValue({
      voices: mockVoices,
      loading: false,
      error: null,
      fetchVoices: vi.fn(),
    });
    (useSynthesis as any).mockReturnValue({
      jobs: mockJobs,
      loading: false,
      error: null,
      currentJob: null,
      createSynthesis: vi.fn().mockResolvedValue(mockJobs[0]),
      fetchJobs: vi.fn(),
      pollJob: vi.fn().mockResolvedValue(mockJobs[0]),
      downloadAudio: vi.fn().mockResolvedValue(new Blob(["audio"], { type: "audio/wav" })),
      deleteJob: vi.fn(),
      setCurrentJob: vi.fn(),
    });
  });

  const renderDashboard = () => {
    return render(
      <BrowserRouter>
        <Dashboard />
      </BrowserRouter>
    );
  };

  test("renders dashboard with text input and voice selector", () => {
    renderDashboard();
    expect(screen.getByLabelText("Text to Synthesize")).toBeInTheDocument();
    expect(screen.getByLabelText("Voice")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /generate speech/i })).toBeInTheDocument();
  });

  test("shows recent jobs table", () => {
    renderDashboard();
    expect(screen.getByText("Recent Synthesis Jobs")).toBeInTheDocument();
    expect(screen.getByText("Hello world")).toBeInTheDocument();
  });

  test("enables generate button when text and voice selected", () => {
    renderDashboard();
    const generateBtn = screen.getByRole("button", { name: /generate speech/i });
    expect(generateBtn).toBeDisabled();

    fireEvent.change(screen.getByLabelText("Text to Synthesize"), { target: { value: "Test text" } });
    expect(generateBtn).toBeDisabled();

    fireEvent.change(screen.getByLabelText("Voice"), { target: { value: "1" } });
    expect(generateBtn).not.toBeDisabled();
  });
});