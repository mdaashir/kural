"""Tests for kural.engine.cues — synthesized musical chimes (Wispr Flow style)."""

import io
import wave

from kural.engine.cues import (
    CUE_NOTES,
    SAMPLE_RATE,
    get_cue_wav_bytes,
    synth_cue_wav,
)


class TestCuesSynthesis:
    def test_cue_notes_defined(self):
        for name in ("start", "stop", "done", "error", "transform"):
            assert name in CUE_NOTES
            assert len(CUE_NOTES[name]) >= 1
            for freq, dur, gain in CUE_NOTES[name]:
                assert freq > 100
                assert dur > 0
                assert 0.0 < gain <= 1.0

    def test_synth_cue_produces_valid_wav(self):
        notes = [(440.0, 0.1, 0.5)]
        wav_bytes = synth_cue_wav(notes)
        assert isinstance(wav_bytes, bytes)
        assert len(wav_bytes) > 44  # WAV header is 44 bytes

        with io.BytesIO(wav_bytes) as buf, wave.open(buf, "rb") as wf:
            assert wf.getnchannels() == 1
            assert wf.getsampwidth() == 2
            assert wf.getframerate() == SAMPLE_RATE
            frames = wf.getnframes()
            assert frames > 0

    def test_get_cue_wav_bytes_caching(self):
        wav1 = get_cue_wav_bytes("start")
        wav2 = get_cue_wav_bytes("start")
        # Cached in memory
        assert wav1 is wav2
        assert len(wav1) > 100

    def test_get_unknown_cue_falls_back_to_done(self):
        wav_unknown = get_cue_wav_bytes("unknown_event_cue")
        assert len(wav_unknown) > 100
