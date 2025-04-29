import ollama
import json
import datetime

class ConversationSummary:
    def __init__(self, summary_file="adaptive_memory/conversation_summary.json"):
        self.summary_file = summary_file
        self.conversation_log = []
        self.load_summary()

    def load_summary(self):
        try:
            with open(self.summary_file, "r") as f:
                data = json.load(f)
                self.conversation_log = data.get("conversation_log", [])
        except FileNotFoundError:
            self.save_summary()

    def save_summary(self):
        data = {
            "conversation_log": self.conversation_log,
            "last_updated": datetime.datetime.now().isoformat()
        }
        with open(self.summary_file, "w") as f:
            json.dump(data, f, indent=4)

    def add_to_log(self, speaker, message):
        timestamp = datetime.datetime.now().isoformat()
        entry = {"timestamp": timestamp, "speaker": speaker, "message": message}
        self.conversation_log.append(entry)
        self.save_summary()

    def generate_summary(self, conversation_list):
        conversation_text = "\n".join(conversation_list)
        prompt = (
            "Summarize the following conversation from your perspective as an advanced AI assistant, "
            "highlighting key insights and points:\n\n"
            f"{conversation_text}\n\nSummary:"
        )
        response = ollama.chat(
            model="llama3.2",
            messages=[{"role": "user", "content": prompt}]
        )
        summary_text = response["message"]["content"]
        self.add_to_log("SUMMARY", summary_text)
        return summary_text

if __name__ == "__main__":
    cs = ConversationSummary()
    print(cs.generate_summary(["Hello", "How are you?"]))
