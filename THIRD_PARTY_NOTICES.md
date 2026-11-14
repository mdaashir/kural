# Third-Party Notices

Kural is built on two MIT-licensed upstream projects. Their copyright lines and
licence texts are reproduced here in full, as required by the MIT licence terms.

---

## 1. drajb/whisper-local

**Origin:** https://github.com/drajb/whisper-local
(itself a fork of Pin Wang's whisper-key-local: https://github.com/pinw/whisper-key-local)

**Upstream commit imported:** `fcd87875ac582e11afc65d916a2bc38bda2b5ad7`

**Copyright:**
> Copyright (c) Pin Wang
> Copyright (c) drajb contributors

**Licence:** MIT

> Permission is hereby granted, free of charge, to any person obtaining a copy
> of this software and associated documentation files (the "Software"), to deal
> in the Software without restriction, including without limitation the rights
> to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
> copies of the Software, and to permit persons to whom the Software is
> furnished to do so, subject to the following conditions:
>
> The above copyright notice and this permission notice shall be included in all
> copies or substantial portions of the Software.
>
> THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
> IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
> FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
> AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
> LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
> OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
> SOFTWARE.

**Files ported from this source:**

| kural path | upstream path |
|---|---|
| `kural/engine/__init__.py` | `src/whisper_key/__init__.py` |
| `kural/engine/audio_recorder.py` | `src/whisper_key/audio_recorder.py` |
| `kural/engine/dictation_cleanup.py` | `src/whisper_key/dictation_cleanup.py` |
| `kural/engine/dictation_languages.py` | `src/whisper_key/dictation_languages.py` |
| `kural/engine/model_registry.py` | `src/whisper_key/model_registry.py` |
| `kural/engine/model_transfer.py` | `src/whisper_key/model_transfer.py` |
| `kural/engine/streaming_delivery.py` | `src/whisper_key/streaming_delivery.py` |
| `kural/engine/streaming_manager.py` | `src/whisper_key/streaming_manager.py` |
| `kural/engine/streaming_recognizer.py` | `src/whisper_key/streaming_recognizer.py` |
| `kural/engine/utils.py` | `src/whisper_key/utils.py` |
| `kural/engine/voice_activity_detection.py` | `src/whisper_key/voice_activity_detection.py` |
| `kural/engine/whisper_engine.py` | `src/whisper_key/whisper_engine.py` |
| `kural/engine/hardware_detection.py` | `src/whisper_key/hardware_detection.py` + `src/whisper_key/platform/windows/gpu.py` |
| `kural/config/config_manager.py` | `src/whisper_key/config_manager.py` |
| `kural/config/defaults_merge.py` | `src/whisper_key/defaults_merge.py` |
| `kural/config/config.defaults.yaml` | `src/whisper_key/config.defaults.yaml` |
| `kural/config/commands.defaults.yaml` | `src/whisper_key/commands.defaults.yaml` |
| `kural/doctor.py` | `src/whisper_key/doctor.py` |

---

## 2. ROHITCRAFTSYT/WhispLocal

**Origin:** https://github.com/ROHITCRAFTSYT/WhispLocal

**Upstream commit imported:** `315af364f9bf3aa61b40092bc258ce88aa67756e`

**Copyright:**
> Copyright (c) Rohit Burani / ROHITCRAFTSYT

**Licence:** MIT

> Permission is hereby granted, free of charge, to any person obtaining a copy
> of this software and associated documentation files (the "Software"), to deal
> in the Software without restriction, including without limitation the rights
> to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
> copies of the Software, and to permit persons to whom the Software is
> furnished to do so, subject to the following conditions:
>
> The above copyright notice and this permission notice shall be included in all
> copies or substantial portions of the Software.
>
> THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
> IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
> FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
> AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
> LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
> OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
> SOFTWARE.

**Files ported from this source:**

| kural path | upstream path |
|---|---|
| `kural/control/guardrails.py` | `whisp/commands.py` + `GUARDRAILS.md` |
| `kural/control/app_index.py` | `whisp/commands.py` + `whisp/appcontext.py` |
| `kural/control/media.py` | `whisp/volume.py` |
| `kural/control/windows.py` | `whisp/commands.py` |
| `kural/control/parser.py` | `whisp/commands.py` |
| `kural/control/executor.py` | `whisp/commands.py` |
| `kural/control/llm_fallback.py` | `whisp/locallm.py` |
| `kural/engine/wake_word.py` | `src/whisper_key/voice_activity_detection.py` + `whisp/` |
| `kural/runtime.py` | `src/whisper_key/state_manager.py` + `whisp/app.py` |
