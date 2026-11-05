"""The agent loop: send the conversation and the tools, run the requested tools, repeat until a text answer (D3)."""
import json
import os

from dotenv import load_dotenv
from openai import OpenAI

from emporio.prompt import build_system_prompt
from emporio.tools import TOOLS, Session, run_tool, today

MAX_STEPS = 8   # tool rounds per message, a guard against loops


class Agent:
    def __init__(self):
        load_dotenv()
        if not os.getenv("OPENAI_API_KEY"):
            raise SystemExit("OPENAI_API_KEY is not set. Copy .env.example to .env and add your key (see README).")
        self.client = OpenAI(base_url=os.getenv("OPENAI_BASE_URL", "https://openrouter.ai/api/v1"))
        self.model = os.getenv("MODEL", "anthropic/claude-haiku-5.5")
        self.session = Session()
        self.messages = [{"role": "system", "content": build_system_prompt(today())}]   # in-memory history (D7)

    def reply(self, text: str) -> str:
        self.messages.append({"role": "user", "content": text})
        for _ in range(MAX_STEPS):
            response = self.client.chat.completions.create(
                model=self.model, messages=self.messages, tools=TOOLS, temperature=0.3)
            message = response.choices[0].message
            if not message.tool_calls:
                answer = message.content or ""
                self.messages.append({"role": "assistant", "content": answer})
                return answer
            # The model asked for tools: record the request, run each tool, send the results back
            self.messages.append({"role": "assistant", "content": message.content or "",
                                  "tool_calls": [c.model_dump() for c in message.tool_calls]})
            for call in message.tool_calls:
                args = json.loads(call.function.arguments or "{}")
                result = run_tool(self.session, call.function.name, args)
                self.session.calls.append((call.function.name, args, result))
                self.messages.append({"role": "tool", "tool_call_id": call.id,
                                      "content": json.dumps(result, ensure_ascii=False)})
        return "Desculpe, não consegui concluir agora. Vou passar sua mensagem para a equipe, tudo bem?"
