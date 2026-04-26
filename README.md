# 🎹 REMI (Runtime Engine for Musical Instruments)

**REMI** is a high-performance polyphonic sampler built for the terminal. Forget bloated GUIs that eat your RAM and lag your workflow. REMI is designed for engineers who want professional-grade sampling without leaving the CLI.

> **🔴 Red Team Warning:** This isn't a toy. If you're looking for shiny gradients and useless animations, move along. We optimize for the event loop, audit for memory leaks, and obsess over latency so your CPU doesn't have to.

---

## 🚀 Why REMI?

Most modern samplers are "God Classes" wrapped in unnecessary abstraction layers. REMI is built with a single obsession: **Performance over Pyrotechnics.**

- **TUI-First:** Built on [Textual](https://textual.textualize.io/) for a fluid, snappy, and hardware-accelerated terminal experience.
- **GIL-Aware Engineering:** **Requires Python 3.11/3.12+**. We take advantage of the latest performance improvements in the Python runtime to ensure the audio thread doesn't choke.
- **Strict Architecture:** Clean separation between `SamplerCore` and the UI. No spaghetti code allowed.
- **Asset Management:** Efficient sample handling designed to load libraries like *Growlybass* without saturating the data bus.
- **Low Latency:** Designed to run on "real-world" hardware (from old ASUS TUF laptops to vintage MacBooks) without audio stuttering.

---

## 🛠️ Technical Stack

- **Runtime:** Python 3.11 / 3.12+ (Mandatory for GIL performance and specialized optimizations).
- **Interface:** Textual (Rich TUI framework).
- **Audio Core:** Focused on buffer management and interrupt-driven logic.
- **Mapping:** Dynamic mapping system for triggering samples via specific MIDI/Keyboard triggers.

---

## 📦 Installation (For the Brave)

1. **Clone the repository:**
   ```bash
   git clone https://github.com/rafaamarin/remi.git
   cd remi
   ```

2. **Set up your environment (don't pollute your system):**
   ```bash
   python3.12 -m venv .venv
   source .venv/bin/activate
   pip install -e .
   ```

3. **Ignite the engine:**
   ```bash
   python main.py
   ```

---

## 💂‍♂️ The Audit Protocol

This repo is not a democracy. Every line of code undergoes a "Red Team" audit to prevent:
- **RAM Leaks:** Especially during asset loading/unloading.
- **Event Loop Blocking:** Synchronous processing is a crime here.
- **Bad OOP Design:** No bloated classes or unnecessary coupling.

If you want to contribute, be prepared for us to tear your PR apart in search of inefficiencies. **We want code that flies.**

---

## 🎹 Included Library: Growlybass
REMI ships with a sample of **Growlybass** for testing. It’s an aggressive, high-character bass—perfect for testing the motor's transient response.

---

## 📄 License
MIT. Do whatever you want, but if you build something amazing, let us know. If the code breaks your machine, don't say we didn't warn you about the performance-first mindset.
