---
title: Generative AI
sidebar_label: Generative AI
---

# Generative AI

The Generative module lets you interact with generative AI models directly inside
dashAI, without writing any code. You can generate text or images, adjust model
parameters in real time, and track every configuration change in a session history.

:::note Hardware requirement
Generative models are computationally intensive. A NVIDIA GPU with CUDA support
is strongly recommended. Running these models on CPU is possible but significantly
slower, and some larger models may fail to load due to memory constraints.
:::

---

## Available Tasks

When you open the Generative module, you select a task type that determines which
models are available:

| Task            | Description                                                                      |
| --------------- | -------------------------------------------------------------------------------- |
| **TextToText**  | Generate text from a text prompt. Includes LLMs such as Qwen, Llama, and others. |
| **TextToImage** | Generate images from a text description using models like Stable Diffusion.      |
| **ControlNet**  | Transform or modify an existing image guided by text and an input image.         |

---

## Step by Step Guide

### 1. Select a Task

Navigate to the **GENERATIVE** section in the top navigation bar.
Click on the task type you want to use (e.g., **TextToText**).

### 2. Select a Model

A list of available models for the selected task is shown. Click on a model to select it.

### 3. Configure Model Parameters

Each model exposes a set of parameters that control its behavior. These appear in a
panel on the right side of the screen. Common parameters include:

| Parameter       | Description                                                                                                                                                                           |
| --------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Temperature** | Controls the randomness of the output. Lower values (e.g., 0.1) produce more deterministic, focused responses. Higher values (e.g., 1.0+) produce more varied and creative outputs.   |
| **Max tokens**  | The maximum number of tokens (roughly words or word pieces) the model will generate in a single response.                                                                             |
| **Top-p**       | Nucleus sampling, which limits generation to the smallest set of tokens whose cumulative probability exceeds this value. Works together with temperature to control output diversity. |
| **Seed**        | A fixed random seed for reproducibility. Setting the same seed with the same parameters will produce the same output.                                                                 |

Parameters vary by model, and not all models expose all of the above. Each parameter has
a **?** help icon that shows a description when hovered.

For image generation tasks, additional parameters are available such as:

- **Width / Height**: output image dimensions. Both must be divisible by 8.
- **Inference steps**: number of denoising steps. More steps generally produce
  higher quality images but take longer.
- **Guidance scale**: how closely the model follows the text prompt.

### 4. Configure Session Parameters

Before creating the session you can optionally set:

- **Session name**: a label to identify this session in the session list.
- **Session description**: an optional note about the purpose of this session.

Both fields are optional. If left empty, dashAI assigns a default name.

### 5. Create the Session

Click **"Create a session"** to initialize the session. dashAI will load the
selected model. This may take a moment, especially on first use when model
weights need to be downloaded.

Once the session is ready, the interaction interface opens.

### 6. Interact with the Model

The main area of the session is the interaction interface:

- **TextToText**: an input field where you type a prompt and receive the model's
  text response. Each exchange is shown as a conversation thread.
- **TextToImage / ControlNet**: an input field for the text prompt and, where
  applicable, an image upload area. The generated image is displayed inline.

Submit your input and wait for the model to generate a response. Generation time
depends on the model size, the parameter configuration, and your hardware.

### 7. Adjust Parameters During the Session

You can change any model parameter at any time during an active session using the
parameter panel on the right. Changes take effect on the next generation, so you do
not need to create a new session.

### 8. View the Session History

Click the **"History"** button to open a log of all parameter changes made during
the session. Each entry shows:

- The parameter that was changed.
- The previous and new values.
- The date and time of the change.

This is useful for tracking what configuration produced a particular output and
for reverting to a previous state.

### 9. Access Previous Sessions

All sessions you have created are listed on the left side of the Generative section,
organized by task type. Click any session to reopen it and continue interacting with
the model using the same configuration.

---

## Tips

- Start with default parameter values and adjust incrementally. Changing multiple
  parameters at once makes it hard to understand which change affected the output.
- For image generation, **width and height must be divisible by 8**. Values that
  don't meet this requirement will cause an error.
- Use a fixed **Seed** when experimenting with parameters. It lets you compare
  outputs from different configurations while holding randomness constant.
- If the model runs out of memory during generation, try reducing **Max tokens**
  (for text) or **Width/Height** and **Inference steps** (for images).
- Session history is particularly useful in a teaching context: it creates a
  visible record of how parameter changes affect model behavior.

## Troubleshooting

| Symptom                                 | Likely cause                                   | Solution                                                                               |
| --------------------------------------- | ---------------------------------------------- | -------------------------------------------------------------------------------------- |
| Generation fails immediately            | Insufficient GPU memory                        | Reduce image dimensions or max tokens; close other GPU intensive applications          |
| Image dimensions error                  | Width or height not divisible by 8             | Adjust dimensions to the nearest multiple of 8 (e.g., 512, 768, 1024)                  |
| Model takes very long to load           | First time use, model weights being downloaded | Wait for the download to complete; subsequent loads will be faster                     |
| Output is always identical              | Seed is fixed and parameters haven't changed   | Change the seed or increase temperature to get varied outputs                          |
| Error details are not visible in the UI | Error modal shows a generic message            | Open the browser developer console (F12) and check the console logs for the full error |
