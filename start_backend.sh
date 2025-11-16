from transformers import AutoModelForCausalLM, AutoTokenizer

model_name = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
save_dir = "~/desktop/hf_models/tinyllama"

print("🔽 Downloading model and tokenizer...")
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name)

print("💾 Saving model locally...")
tokenizer.save_pretrained(save_dir)
model.save_pretrained(save_dir)
print(f"✅ Model saved at: {save_dir}")