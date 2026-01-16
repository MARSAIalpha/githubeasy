# LM Studio Setup & RAG Guide

## 1. Exposing Local AI to the Network (API Access)
To let your News System (on another machine or process) talk to "AI395":

1.  **Open LM Studio**.
2.  Go to the **Local Server** (Developer) tab (usually the `<->` icon).
3.  Look for **"Server Options"** or **"Configuration"**.
4.  **Network Interface / Host**: Change this from `localhost` (or `127.0.0.1`) to `0.0.0.0` (or `Any`).
    *   *Why?* This allows requests from other computers on your Wi-Fi/LAN.
5.  **Port**: Note the port (default is `1234`).
6.  **Start Server**: Click "Start Server".
7.  **Find your IP**: Open a terminal (Powershell) on this machine and type `ipconfig`. Look for "IPv4 Address" (e.g., `192.168.1.15`).
8.  **Connection String**: Your API Base URL for other machines is: `http://192.168.1.15:1234/v1`

## 2. Memory Allocation (AI395)
To ensure your "AI395" machine uses its full power (GPU/RAM) for the model:

1.  **Load a Model** in LM Studio.
2.  Look at the **Right Sidebar** (Settings).
3.  **GPU Offload**:
    *   Find the slider for "GPU Offload".
    *   Slide it to **Max** (connects all layers to GPU) if you have a good graphics card.
    *   If the bar is green, you are good. If it goes red (VRAM exceeded), lower it slightly.
4.  **Context Length**:
    *   Increase this if you need to process long news articles.
    *   Typical starts: `4096` or `8192`.
    *   *Warning*: Higher context uses more RAM.

## 3. What is RAG? (Retrieval-Augmented Generation)
Your models (Llama 3, Mistral, etc.) have a "Knowledge Cutoff". They don't know today's news. **RAG** bridges this gap.

**The Workflow implemented in this project:**
1.  **Question**: User asks "what happened in the stock market today?"
2.  **Retrieve (The "Search" part)**:
    *   Python script uses `duckduckgo-search` to query the live internet.
    *   We get back snippets of text from *current* websites.
3.  **Augment (The "Context" part)**:
    *   We wrap the user's question with these snippets.
    *   *Prompt*: "Based on this news: [Snippet 1, Snippet 2], answer the question: [User Question]"
4.  **Generate (The "AI" part)**:
    *   We send this giant prompt to your LM Studio Local Server.
    *   The AI summarizes the *fresh* news for you.

You essentially turn the AI from a "Encyclopaedia from 2023" into a "Smart Reader of Today's Newspaper".
