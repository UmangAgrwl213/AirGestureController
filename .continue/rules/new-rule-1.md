# Kimi Setup Notes (Continue + NVIDIA)

## Recommended models
- Primary: `moonshotai/kimi-k2.6`
- Fallback (more stable for coding): `moonshotai/kimi-k2-instruct`

## Known symptoms
- Garbled mixed-language output (including Chinese bursts)
- Repeated tokens / nonsense loops
- Leaked tool-format text in normal chat
- Long hangs or no response

## Stable config baseline
Use these values in Continue model config:
- `provider: nvidia`
- `temperature: 0`
- `topP: 0.7`
- `maxTokens: 1024`
- `request timeout: 120000-180000 ms`
- `extraBody.chat_template_kwargs.thinking: false`
- `stop: ["<reserved_token_163777>"]`

## Practical rules
- Use `kimi-k2.6` for general chat.
- Switch to `kimi-k2-instruct` for agent/tool-heavy coding tasks if output gets unstable.
- Keep prompts plain text; avoid pasting raw tool-call protocol blocks into normal chat.
- Restart/reload Continue after major model config changes.

## Quick troubleshoot
1. If response is gibberish, regenerate once.
2. If still bad, switch model to `kimi-k2-instruct`.
3. If still bad, restart Continue and retry.
4. If requests hang, increase timeout and reduce context size.
