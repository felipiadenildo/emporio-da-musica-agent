"""Command-line chat. --debug shows the tool calls, --save writes the conversation to Markdown (D6)."""
import argparse
import json
from datetime import datetime
from pathlib import Path

from emporio.agent import Agent


def _short(value, limit=300) -> str:
    text = json.dumps(value, ensure_ascii=False)
    return text if len(text) <= limit else text[:limit] + "..."


def main():
    parser = argparse.ArgumentParser(description="Empório da Música customer service agent")
    parser.add_argument("--debug", action="store_true", help="print the tool calls and their results")
    parser.add_argument("--save", metavar="FILE", help="save the conversation to a Markdown file at the end")
    args = parser.parse_args()

    agent = Agent()
    transcript = [f"# Conversation ({datetime.now():%Y-%m-%d %H:%M}, model `{agent.model}`)\n"]
    print("Empório da Música: assistente virtual. Digite 'sair' para encerrar.\n")
    while True:
        try:
            text = input("Você: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not text:
            continue
        if text.lower() in {"sair", "exit", "quit"}:
            break
        first_call = len(agent.session.calls)
        answer = agent.reply(text)
        calls = agent.session.calls[first_call:]
        if args.debug:
            for name, call_args, result in calls:
                print(f"  [tool] {name}({_short(call_args)}) -> {_short(result)}")
        print(f"\nEmpório: {answer}\n")
        transcript.append(f"**Cliente:** {text}\n")
        if calls:
            transcript.append("> Tools: " + "; ".join(f"`{name}({_short(a, 120)})`" for name, a, _ in calls) + "\n")
        transcript.append(f"**Empório:** {answer}\n")

    if args.save:
        Path(args.save).parent.mkdir(parents=True, exist_ok=True)
        Path(args.save).write_text("\n".join(transcript), encoding="utf-8")
        print(f"Conversation saved to {args.save}")
