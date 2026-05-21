import os
import threading
import sys
import customtkinter as ctk
from tkinter import filedialog, messagebox

# Import audio processor immediately (doesn't need API keys)
from src.meeting_audio_processor import record_system_audio

class MeetingFulApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("MeetingFul AI Assistant")
        self.geometry("1000x750")
        
        # Set theme
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")
        
        # Set Icon
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "images", "logo.ico")
        if os.path.exists(icon_path):
            try:
                self.iconbitmap(icon_path)
            except Exception:
                pass
        
        self.audio_path = None
        self.transcript = None
        self.rag_chain = None
        self.stop_recording_event = threading.Event()
        self.is_recording = False
        
        # Hide main window until API keys are set
        self.withdraw()
        self.prompt_api_keys()

    def prompt_api_keys(self):
        self.api_window = ctk.CTkToplevel(self)
        self.api_window.title("Enter API Keys")
        self.api_window.geometry("450x300")
        self.api_window.resizable(False, False)
        self.api_window.grab_set()
        self.api_window.protocol("WM_DELETE_WINDOW", self.on_api_window_close)
        
        ctk.CTkLabel(self.api_window, text="Welcome to MeetingFul!", font=("Arial", 20, "bold")).pack(pady=(20, 10))
        
        ctk.CTkLabel(self.api_window, text="Groq API Key (Transcription/Translation):").pack(anchor="w", padx=20)
        self.groq_entry = ctk.CTkEntry(self.api_window, show="*", width=410)
        self.groq_entry.pack(pady=(0, 15), padx=20)
        
        ctk.CTkLabel(self.api_window, text="Mistral API Key (Summarization/RAG):").pack(anchor="w", padx=20)
        self.mistral_entry = ctk.CTkEntry(self.api_window, show="*", width=410)
        self.mistral_entry.pack(pady=(0, 20), padx=20)
        
        ctk.CTkButton(self.api_window, text="Start Application", command=self.save_api_keys).pack()

    def on_api_window_close(self):
        self.destroy()
        sys.exit(0)

    def save_api_keys(self):
        groq_key = self.groq_entry.get().strip()
        mistral_key = self.mistral_entry.get().strip()
        
        if not groq_key or not mistral_key:
            messagebox.showerror("Error", "Both API keys are required.")
            return
            
        os.environ["GROQ_API_KEY"] = groq_key
        os.environ["MISTRAL_API_KEY"] = mistral_key
        
        self.api_window.destroy()
        self.deiconify() 
        self.build_main_ui()

    def build_main_ui(self):
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        
        # Sidebar
        self.sidebar_frame = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(6, weight=1)
        
        ctk.CTkLabel(self.sidebar_frame, text="MeetingFul", font=("Arial", 24, "bold")).grid(row=0, column=0, padx=20, pady=(20, 10))
        
        ctk.CTkLabel(self.sidebar_frame, text="Settings:", font=("Arial", 16, "bold")).grid(row=1, column=0, padx=20, pady=(10, 0), sticky="w")
        
        ctk.CTkLabel(self.sidebar_frame, text="Processing Mode:").grid(row=4, column=0, padx=20, pady=(10, 0), sticky="w")
        self.mode_var = ctk.StringVar(value="Transcribe")
        self.mode_menu = ctk.CTkOptionMenu(self.sidebar_frame, values=["Transcribe", "Translate"], variable=self.mode_var)
        self.mode_menu.grid(row=5, column=0, padx=20, pady=(0, 10), sticky="ew")
        
        # Audio Actions
        self.record_btn = ctk.CTkButton(self.sidebar_frame, text="⏺ Record System Audio", fg_color="red", hover_color="#aa0000", command=self.toggle_recording)
        self.record_btn.grid(row=7, column=0, padx=20, pady=10, sticky="ew")
        
        self.upload_btn = ctk.CTkButton(self.sidebar_frame, text="📁 Upload Audio", command=self.upload_audio)
        self.upload_btn.grid(row=8, column=0, padx=20, pady=10, sticky="ew")
        
        self.process_btn = ctk.CTkButton(self.sidebar_frame, text="⚙️ Process Audio", command=self.start_processing, state="disabled")
        self.process_btn.grid(row=9, column=0, padx=20, pady=20, sticky="ew")

        # Main Content Area
        self.main_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.main_frame.grid_rowconfigure(1, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)
        
        # Status Log
        self.status_log = ctk.CTkTextbox(self.main_frame, height=100)
        self.status_log.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        self.status_log.insert("0.0", "Welcome to MeetingFul. Waiting for audio input...\n")
        self.status_log.configure(state="disabled")
        
        # Tabs for Results
        self.tabview = ctk.CTkTabview(self.main_frame)
        self.tabview.grid(row=1, column=0, sticky="nsew")
        
        self.tabview.add("Transcript")
        self.tabview.add("Summary")
        self.tabview.add("Action Items")
        self.tabview.add("Decisions")
        self.tabview.add("Open Questions")
        self.tabview.add("RAG Q&A")
        
        # Add Textboxes to tabs
        self.result_boxes = {}
        for tab_name in ["Transcript", "Summary", "Action Items", "Decisions", "Open Questions"]:
            box = ctk.CTkTextbox(self.tabview.tab(tab_name))
            box.pack(fill="both", expand=True, padx=10, pady=10)
            self.result_boxes[tab_name] = box
            
        # RAG Q&A Tab layout
        rag_tab = self.tabview.tab("RAG Q&A")
        self.chat_history = ctk.CTkTextbox(rag_tab, state="disabled")
        self.chat_history.pack(fill="both", expand=True, padx=10, pady=(10, 5))
        
        self.chat_input = ctk.CTkEntry(rag_tab, placeholder_text="Ask a question about the transcript...")
        self.chat_input.pack(fill="x", padx=10, pady=(0, 10))
        self.chat_input.bind("<Return>", self.ask_question)
        
    def log(self, message):
        self.status_log.configure(state="normal")
        self.status_log.insert("end", message + "\n")
        self.status_log.see("end")
        self.status_log.configure(state="disabled")

    def toggle_recording(self):
        if not self.is_recording:
            self.is_recording = True
            self.record_btn.configure(text="⏹ Stop Recording", fg_color="darkred")
            self.upload_btn.configure(state="disabled")
            self.process_btn.configure(state="disabled")
            self.stop_recording_event.clear()
            self.log("[INFO] Started system audio recording...")
            threading.Thread(target=self.record_audio_thread, daemon=True).start()
        else:
            self.log("[INFO] Stopping recording...")
            self.stop_recording_event.set()

    def record_audio_thread(self):
        try:
            path = record_system_audio(stop_event=self.stop_recording_event)
            self.audio_path = path
            
            def on_recording_complete():
                self.is_recording = False
                self.record_btn.configure(text="⏺ Record System Audio", fg_color="red")
                self.upload_btn.configure(state="normal")
                if path:
                    self.log(f"[SUCCESS] Audio recorded to {path}")
                    self.process_btn.configure(state="normal")
                else:
                    self.log("[ERROR] Recording failed or was empty.")
                    
            self.after(0, on_recording_complete)
        except Exception as e:
            err = f"[ERROR] {e}"
            self.after(0, lambda msg=err: self.log(msg))

    def upload_audio(self):
        path = filedialog.askopenfilename(filetypes=[("Audio Files", "*.mp3 *.wav *.m4a")])
        if path:
            self.audio_path = path
            self.log(f"[INFO] Selected audio: {path}")
            self.process_btn.configure(state="normal")

    def start_processing(self):
        if not self.audio_path:
            return
            
        self.record_btn.configure(state="disabled")
        self.upload_btn.configure(state="disabled")
        self.process_btn.configure(state="disabled")
        
        # Clear previous results
        for box in self.result_boxes.values():
            box.configure(state="normal")
            box.delete("0.0", "end")
            box.configure(state="disabled")
            
        self.chat_history.configure(state="normal")
        self.chat_history.delete("0.0", "end")
        self.chat_history.configure(state="disabled")
        
        chunk_mins = 10
            
        mode = self.mode_var.get().lower()
        
        threading.Thread(target=self.processing_thread, args=(self.audio_path, chunk_mins, mode), daemon=True).start()

    def processing_thread(self, audio_path, chunk_mins, mode):
        # We import these here so that os.environ modifications have taken effect
        from src.audio_splitter import chunk_audio
        from src.audio_transcriber import transcribe_chunked_audio
        from src.audio_translator import translate_chunked_audio
        from src.meeting_summarizer import summarize_transcript
        from src.rag_pipeline import rag_engine
        
        try:
            self.after(0, lambda: self.log("[INFO] Splitting audio into chunks..."))
            chunk_paths = chunk_audio(audio_path, chunk_minutes=chunk_mins)
            
            if not chunk_paths:
                self.after(0, lambda: self.log("[ERROR] Failed to chunk audio."))
                return
                
            self.after(0, lambda: self.log(f"[INFO] Transcribing audio ({mode} mode)..."))
            if mode == "translate":
                self.transcript = translate_chunked_audio(chunk_paths)
            else:
                self.transcript = transcribe_chunked_audio(chunk_paths)
                
            if not self.transcript:
                self.after(0, lambda: self.log("[ERROR] Transcription failed or is empty."))
                return
                
            self.after(0, lambda: self.set_result_text("Transcript", self.transcript))
            
            self.after(0, lambda: self.log("[INFO] Generating summaries..."))
            try:
                summary_result = summarize_transcript(self.transcript)
                
                self.after(0, lambda: self.set_result_text("Summary", summary_result.get("summary", "")))
                self.after(0, lambda: self.set_result_text("Action Items", summary_result.get("action_items", "")))
                self.after(0, lambda: self.set_result_text("Decisions", summary_result.get("key_decisions", "")))
                self.after(0, lambda: self.set_result_text("Open Questions", summary_result.get("open_questions", "")))
            except Exception as e:
                err = f"[WARNING] Summarization failed: {e}"
                self.after(0, lambda msg=err: self.log(msg))
                msg = "summary failed, go to the chat section to chat"
                self.after(0, lambda m=msg: self.set_result_text("Summary", m))
                self.after(0, lambda m=msg: self.set_result_text("Action Items", m))
                self.after(0, lambda m=msg: self.set_result_text("Decisions", m))
                self.after(0, lambda m=msg: self.set_result_text("Open Questions", m))
            
            self.after(0, lambda: self.log("[INFO] Initializing RAG engine..."))
            try:
                self.rag_chain = rag_engine(self.transcript)
            except Exception as e:
                err = f"[ERROR] RAG initialization failed: {e}"
                self.after(0, lambda msg=err: self.log(msg))
                
            self.after(0, lambda: self.log("[SUCCESS] Processing complete!"))
            
        except Exception as e:
            err = f"[ERROR] Exception during processing: {e}"
            self.after(0, lambda msg=err: self.log(msg))
        finally:
            self.after(0, self.reset_buttons)

    def set_result_text(self, tab, text):
        text = text.replace("*", "").replace("#", "")
        box = self.result_boxes[tab]
        box.configure(state="normal")
        box.insert("0.0", text)
        box.configure(state="disabled")

    def reset_buttons(self):
        self.record_btn.configure(state="normal")
        self.upload_btn.configure(state="normal")
        self.process_btn.configure(state="normal")

    def ask_question(self, event):
        question = self.chat_input.get().strip()
        if not question or not self.rag_chain:
            return
            
        self.chat_input.delete(0, "end")
        
        self.chat_history.configure(state="normal")
        self.chat_history.insert("end", f"You: {question}\n\n")
        self.chat_history.see("end")
        self.chat_history.configure(state="disabled")
        
        threading.Thread(target=self.rag_thread, args=(question,), daemon=True).start()
        
    def rag_thread(self, question):
        try:
            result = self.rag_chain.invoke({"input": question})
            
            if isinstance(result, str):
                answer = result
            else:
                answer = result.get("answer") or result.get("result") or result.get("output") or str(result)
                
            self.after(0, lambda a=answer: self.add_rag_answer(a))
        except Exception as e:
            err = f"Error: {e}"
            self.after(0, lambda a=err: self.add_rag_answer(a))
            
    def add_rag_answer(self, answer):
        answer = answer.replace("*", "").replace("#", "")
        self.chat_history.configure(state="normal")
        self.chat_history.insert("end", f"MeetingFul: {answer}\n\n")
        self.chat_history.see("end")
        self.chat_history.configure(state="disabled")

if __name__ == "__main__":
    app = MeetingFulApp()
    app.mainloop()
