# LLM Provider Facts — OpenCode Zen / DeepSeek V4-Flash

Verified 2026-08-08 against opencode.ai docs, DeepSeek API docs, and third-party adapter reports.

## Endpoint

| Item | Value |
|---|---|
| Base URL | `https://opencode.ai/zen/v1` (OpenAI-compatible) |
| Chat endpoint | `POST https://opencode.ai/zen/v1/chat/completions` |
| Model ID | `deepseek-v4-flash-free` |
| Model catalog | `GET https://opencode.ai/zen/v1/models` |
| Auth | Bearer key (OpenCode Zen API key) |
| SDK | Standard OpenAI SDK with `base_url` override (`@ai-sdk/openai-compatible` in JS) |

## What the free alias actually serves

`deepseek-v4-flash-free` maps in-place to the official `deepseek-v4-flash`
(DeepSeek-V4-Flash-0731 checkpoint): 1M context, 384K max output, thinking mode
on by default (`reasoning_content` in responses; disable with
`extra_body={"thinking": {"type": "disabled"}}`). DeepSeek retired the legacy
`deepseek-chat` / `deepseek-reasoner` IDs on 2026-07-24.

## Caveats

1. **JSON mode through the gateway is not guaranteed.** Zen advertises
   `response_format: {"type": "json_schema", ...}`, but adapter smoke probes
   show model-dependent behavior behind the same gateway: `deepseek-v4-pro`
   rejected `response_format` ("response_format type is unavailable now");
   other models accepted it but silently returned non-JSON. **Design for
   function/tool calling (supported, client-side loop) or plain-prompt JSON +
   Pydantic validation + retries. Smoke-test `deepseek-v4-flash-free` against
   the real slot-filling schema before committing to a mechanism.**
2. **Free tier is temporary.** OpenCode offers the `-free` alias "for a limited
   time" (feedback collection). Keep the model ID in config, not code. Paid
   fallbacks: Zen `deepseek-v4-flash` (per-token) or DeepSeek direct at
   `https://api.deepseek.com` ($0.14 / $0.28 per 1M input/output, cache-hit
   input $0.0028).
3. **Possible account toggle.** Free/China-hosted models may require the
   "Enable models hosted in China" setting in the OpenCode web backend; a 404
   on the model is the symptom.
4. **No server-side sessions** on the chat/completions transport — send full
   context each call (fine for our single-shot classify + slot-fill usage).
5. **Egress reminder (ADR 0001):** only schema, template descriptions, and the
   user's question go to this API — never patient rows.
