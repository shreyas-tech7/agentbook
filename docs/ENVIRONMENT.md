# Environment

Probes run with `curl -sS -o /dev/null -w '%{http_code}' -m 10 <url>` on 2026-11-20.

| Host | Result |
| --- | --- |
| https://pypi.org/pypi/agentbook/json | 404 (name free) |
| https://registry.npmjs.org/agentbook | 404 (name free) |
| https://registry.npmjs.org/patternbook | 200 (taken) |
| https://www.anthropic.com/research/building-effective-agents | 200 |
| https://api.groq.com/openai/v1/models | blocked: CONNECT tunnel failed, response 403 |
| https://openrouter.ai/api/v1/models | blocked: CONNECT tunnel failed, response 403 |
| https://huggingface.co | no answer (000) |
| https://api.osv.dev | no answer (000) |
| https://semgrep.dev | no answer (000) |
| api.github.com for this repo | refused, no repo attached to the session |

Machine: Intel(R) Xeon(R) Processor @ 2.10GHz, 4 cores, Python 3.13 on the VM. CI targets Python 3.11.
No provider key variable was set.
