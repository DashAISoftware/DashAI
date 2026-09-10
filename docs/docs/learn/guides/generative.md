---
title: "Module Guide: Generative AI"
sidebar_label: Generative AI
sidebar_position: 3
---

# Module Guide: Generative AI

The Generative module provides a no code interface for interacting with generative AI models: text generation, image synthesis, and ControlNet conditioned image generation. Unlike the Models module which is built around structured training and evaluation, the Generative module is oriented around interactive experimentation: you configure a model, create a session, and interact with the model in real time while adjusting parameters and observing their effect.

---

## Tasks and Models

The module is organized by task type. Selecting a task filters the available models to those compatible with that generation modality.

### TextToTextGenerationTask

Generates text from a text prompt. Suitable for open ended generation, summarization, instruction following, and question answering.

| Model       | Description                                                                                         |
| ----------- | --------------------------------------------------------------------------------------------------- |
| `QwenModel` | Qwen series language model. Supports instruction following and conversational generation            |
| Other LLMs  | Additional text models may be available depending on your dashAI installation and installed plugins |

### TextToImageGenerationTask

Generates images from a text description.

| Model                    | Description                                                          |
| ------------------------ | -------------------------------------------------------------------- |
| `StableDiffusionV2Model` | Stable Diffusion v2 for general purpose text-to-image synthesis      |
| `StableDiffusionV3Model` | Stable Diffusion v3 with improved prompt adherence and image quality |

### ControlNetTask

Generates images guided by both a text prompt and a spatial control image (e.g., a pose, depth map, or edge map). Gives precise control over the structure of the generated image.

| Model                           | Description                                                                   |
| ------------------------------- | ----------------------------------------------------------------------------- |
| `StableDiffusionXLV1ControlNet` | SDXL based model with ControlNet conditioning for structured image generation |

---

## Session Model

The Generative module uses a **session** concept that differs from the Models module. Here, a session is a persistent conversation thread tied to a specific model and parameter configuration. Each session stores the full interaction history and the complete log of parameter changes made during that session.

Sessions are listed on the left side of the Generative section, organized by task. You can maintain multiple sessions per task, each with a different model or configuration.

---

## Parameters

Parameters are configured before creating a session and can be adjusted at any time during an active session. Changes take effect on the next generation, and no restart is required.

### Text Generation Parameters

| Parameter       | What it controls                                                                                                                                                                                                                                    |
| --------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Temperature** | Output randomness. Low values (0.1–0.3) produce focused, deterministic outputs. High values (0.8–1.5+) increase variety and creativity but may reduce coherence                                                                                     |
| **Max Tokens**  | Maximum number of tokens generated per response. One token is roughly ¾ of a word in English. Controls output length and memory usage                                                                                                               |
| **Top-p**       | Nucleus sampling threshold. The model considers only the smallest set of tokens whose cumulative probability reaches this value. Works together with Temperature, since lowering Top-p makes outputs more conservative independently of Temperature |
| **Seed**        | Fixed random seed. Setting the same seed with the same parameters and prompt will reproduce the same output exactly, which is useful for controlled comparisons                                                                                     |

### Image Generation Parameters

| Parameter           | What it controls                                                                                                                                              |
| ------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Width / Height**  | Output image dimensions in pixels. **Both values must be divisible by 8.** Common values: 512, 768, 1024                                                      |
| **Inference Steps** | Number of denoising iterations. More steps produce higher quality and detail but increase generation time. Typical range: 20–50                               |
| **Guidance Scale**  | How strongly the model follows the text prompt vs. free generation. Higher values (7–15) adhere more closely to the prompt; lower values allow more variation |
| **Seed**            | Fixed seed for reproducible image generation                                                                                                                  |

### ControlNet Additional Parameters

When using ControlNet models, additional parameters control the conditioning strength and the processing applied to the control image (e.g., edge detection, depth estimation). These vary by the specific ControlNet variant being used.

---

## Parameter Interaction Effects

Understanding how parameters interact helps avoid common pitfalls:

**Temperature + Top-p:** These two parameters both control output diversity but through different mechanisms. Temperature scales the probability distribution (high = flatter = more random); Top-p truncates the candidate pool. Using both at high values simultaneously can produce incoherent outputs. A common effective combination is moderate temperature (0.7) with Top-p around 0.9.

**Inference Steps + Guidance Scale (image):** More inference steps allow the model to refine details progressively. Higher guidance scale requires more steps to converge properly. Using high guidance with very few steps often produces oversaturated or artifact heavy images.

**Width × Height × Inference Steps (image):** Generation time and memory usage scale with all three. Start with 512×512 and 20–30 steps when testing prompts, then increase resolution and steps for final outputs.

---

## Session History

Every session maintains a complete audit log of parameter changes. Click **History** to view:

- Which parameter was changed
- The value before and after the change
- The timestamp of the change

This log is valuable for retracing the path to a particular output. When you find a generation that works well, the history shows exactly which parameter values produced it.

---

## Hardware Considerations

Generative models have significantly higher hardware requirements than classical ML models.

:::note
A NVIDIA GPU with CUDA support is strongly recommended. Most text generation models (Qwen) require at minimum 8GB VRAM. Image generation models (Stable Diffusion) typically require 6–12GB depending on resolution and model version. Running on CPU is technically possible but practically slow.
:::

**Memory management tips:**

- Reduce **Width/Height** to lower VRAM usage for image models
- Reduce **Max Tokens** to limit memory for text models
- Avoid running multiple generative sessions simultaneously
- If a generation fails with a memory error, reducing any of the above parameters is the first step

**Error visibility:** When a generation fails, the error modal in dashAI shows a generic message. For detailed error information, open the browser developer console (F12 → Console tab) where the full stack trace is logged.

---

## Tips

- Use **Seed** when comparing the effect of a single parameter: fix the seed, change only one parameter, and compare outputs directly.
- For image generation, establish a good prompt at low resolution (512×512, 20 steps) before scaling up. High resolution generation with a bad prompt wastes time and memory.
- The **History** log doubles as a recipe: when you find a configuration that works, the log gives you the exact parameter values to reproduce it in a new session.
- ControlNet models require a control image that matches the conditioning type. A pose model needs a pose skeleton image, and an edge model needs an edge detected image. Providing the wrong type produces incoherent outputs.
- Lower **Guidance Scale** (4–6) often produces more aesthetically pleasing images for creative prompts; higher values (10–15) work better for highly specific or technical prompts.
