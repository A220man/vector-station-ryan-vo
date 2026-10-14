import { useState, useCallback } from "react";
import { api } from "../api/client";
import type { SynthesisJob, SynthesisJobCreate, Voice } from "../types/api";

export function useSynthesis() {
  const [jobs, setJobs] = useState<SynthesisJob[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [currentJob, setCurrentJob] = useState<SynthesisJob | null>(null);

  const createSynthesis = useCallback(async (data: SynthesisJobCreate) => {
    setLoading(true);
    setError(null);
    try {
      const job = await api.createSynthesis(data);
      setJobs((prev) => [job, ...prev]);
      setCurrentJob(job);
      return job;
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Failed to create synthesis";
      setError(message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchJobs = useCallback(async (params?: { page?: number; page_size?: number; status?: string; voice_id?: number }) => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.listSynthesisJobs(params);
      setJobs(response.jobs);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Failed to fetch jobs";
      setError(message);
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchJob = useCallback(async (id: number) => {
    setLoading(true);
    setError(null);
    try {
      const job = await api.getSynthesisJob(id);
      setCurrentJob(job);
      setJobs((prev) => prev.map((j) => (j.id === id ? job : j)));
      return job;
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Failed to fetch job";
      setError(message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const pollJob = useCallback(
    async (jobId: number, intervalMs = 2000, maxAttempts = 60): Promise<SynthesisJob> => {
      for (let attempt = 0; attempt < maxAttempts; attempt++) {
        const job = await fetchJob(jobId);
        if (job.status === "completed" || job.status === "failed") {
          return job;
        }
        await new Promise((resolve) => setTimeout(resolve, intervalMs));
      }
      throw new Error("Synthesis timed out");
    },
    [fetchJob]
  );

  const downloadAudio = useCallback(async (jobId: number): Promise<Blob> => {
    return api.downloadSynthesisAudio(jobId);
  }, []);

  const deleteJob = useCallback(async (jobId: number) => {
    setLoading(true);
    setError(null);
    try {
      await api.deleteSynthesisJob(jobId);
      setJobs((prev) => prev.filter((j) => j.id !== jobId));
      if (currentJob?.id === jobId) setCurrentJob(null);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Failed to delete job";
      setError(message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [currentJob]);

  return {
    jobs,
    loading,
    error,
    currentJob,
    createSynthesis,
    fetchJobs,
    fetchJob,
    pollJob,
    downloadAudio,
    deleteJob,
    setCurrentJob,
  };
}

export function useVoices() {
  const [voices, setVoices] = useState<Voice[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchVoices = useCallback(async (params?: { voice_type?: string; language?: string; is_active?: boolean }) => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.listVoices(params);
      setVoices(response.voices);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Failed to fetch voices";
      setError(message);
    } finally {
      setLoading(false);
    }
  }, []);

  return {
    voices,
    loading,
    error,
    fetchVoices,
  };
}