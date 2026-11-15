"""Tests for kural.engine.adaptive — word frequency learning and automatic corrections."""

from kural.engine.adaptive import AdaptiveLearner, _tokenize


class TestAdaptiveTokenizer:
    def test_tokenize_filters_stopwords_and_digits(self):
        text = "Hello world the and for 12345 Tamil குரல்"
        tokens = _tokenize(text)
        assert "Hello" in tokens
        assert "world" in tokens
        assert "Tamil" in tokens
        assert "குரல்" in tokens
        assert "12345" not in tokens
        assert "the" not in tokens


class TestAdaptiveLearner:
    def test_learn_words_increases_frequency(self, tmp_path):
        learner = AdaptiveLearner(storage_dir=tmp_path)
        assert learner.get_adaptive_hotwords() == []

        # Dictate 3 times so words exceed threshold
        for _ in range(3):
            learner.learn_text("Deep Learning neural network architecture")

        hotwords = learner.get_adaptive_hotwords()
        assert "Learning" in hotwords or "neural" in hotwords

    def test_teach_and_apply_corrections(self, tmp_path):
        learner = AdaptiveLearner(storage_dir=tmp_path)
        learner.teach_correction("cural", "Kural")
        learner.teach_correction("ashir", "Aashir")

        raw_text = "I love cural dictation developed by ashir"
        corrected = learner.apply_corrections(raw_text)
        assert corrected == "I love Kural dictation developed by Aashir"

    def test_corrections_persist_to_disk(self, tmp_path):
        learner1 = AdaptiveLearner(storage_dir=tmp_path)
        learner1.teach_correction("pythan", "Python")

        # Reload from disk
        learner2 = AdaptiveLearner(storage_dir=tmp_path)
        assert learner2.apply_corrections("learning pythan code") == "learning Python code"
