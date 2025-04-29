import os
import json
import time
import requests
import chromadb
from summary import ConversationSummary

class EONMemoryManager:
    def __init__(self, db_path="adaptive_memory/eon_memory.json", token_limit=8000):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.token_limit = token_limit
        self.conversation_summary = ConversationSummary()
        self.chroma_client = chromadb.PersistentClient(path="adaptive_memory/eon_db")
        self.collection = self.chroma_client.get_or_create_collection(name="EON_COLLECTION")
        self.memory = {"conversation_log": []}
        self.load_memory()

    def save_memory(self):
        data = self.collection.get()
        data["conversation_log"] = self.memory["conversation_log"]
        with open(self.db_path, "w") as f:
            json.dump(data, f)

    def load_memory(self):
        if os.path.exists(self.db_path):
            try:
                with open(self.db_path, "r") as f:
                    data = json.load(f)
                if "conversation_log" in data:
                    self.memory["conversation_log"] = data["conversation_log"]
                if "documents" in data and "ids" in data:
                    self.collection.upsert(documents=data["documents"], ids=data["ids"])
            except Exception as e:
                print(f"Error loading memory: {e}")

    def add_memory(self, text, memory_id):
        try:
            self.collection.upsert(documents=[text], ids=[memory_id])
            self.save_memory()
        except Exception as e:
            print(f"Error adding memory: {e}")

    def append_conversation(self, user_message, eon_response):
        self.memory["conversation_log"].append({"user": user_message, "eon": eon_response})
        self.save_memory()

    def retrieve_memory(self, query_text, top_k=3):
        try:
            results = self.collection.query(query_texts=[query_text], n_results=top_k)
            if results and "documents" in results and results["documents"]:
                return results["documents"][0]
        except Exception as e:
            print(f"Error retrieving memory: {e}")
        return []

    def get_total_tokens(self):
        all_docs = self.collection.get().get("documents", [])
        total_tokens = sum(len(doc.split()) for doc in all_docs)
        return total_tokens

    def summarize_memory(self):
        all_docs = self.collection.get().get("documents", [])
        conversation_text = "\n".join(all_docs)
        summary = self.conversation_summary.generate_summary([conversation_text])
        return summary

    def summarize_memory_if_needed(self):
        total_tokens = self.get_total_tokens()
        if total_tokens > self.token_limit:
            print(f"Token limit exceeded: {total_tokens} tokens. Summarizing memories.")
            summary = self.summarize_memory()
            old_ids = self.collection.get().get("ids", [])
            for mid in old_ids:
                try:
                    self.collection.delete(ids=[mid])
                except Exception as e:
                    print(f"Error deleting memory {mid}: {e}")
            self.add_memory(summary, f"summary_{int(time.time())}")
            print("Memory summarized and updated.")

    def check_internet(self, timeout=5):
        try:
            requests.get("https://www.google.com", timeout=timeout)
            return True
        except requests.RequestException:
            return False

    def dynamic_update(self):
        if self.check_internet():
            try:
                response = requests.get("https://api.duckduckgo.com/?q=latest+news&format=json", timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    abstract = data.get("Abstract", "")
                    self.add_memory(abstract, f"news_{int(time.time())}")
                    print("Online data added to memory.")
            except Exception as e:
                print(f"Error fetching online data: {e}")
        else:
            print("No internet connection available.")
        self.summarize_memory_if_needed()

    def recall_past_conversations(self, last_n=5):
        return self.memory.get("conversation_log", [])[-last_n:]
