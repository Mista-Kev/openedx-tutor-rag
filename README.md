# Open edX RAG

This repo is for our student project where we:

- Run **Open edX** locally with Tutor.
- Run a vector database (Qdrant) next to it.
- Pull course content from MongoDB, turn it into embeddings, and store it in Qdrant.
- Build a small Streamlit app where you can ask questions about a course and get answers based on the actual course content.

It’s meant for beginners (including us), so the steps below try to be very explicit.


---

## 1. What this project does (in plain language)

The idea:

1. Open edX stores course content (texts, units, etc.) in MongoDB.
2. We copy this content out, clean it and split it into chunks (e.g. paragraph‑sized).
3. We send each chunk to an embedding model to get a vector (a list of numbers that represent the meaning of the text).
4. We store those vectors in Qdrant (a vector database).
5. When a learner asks a question:
   - We embed the question.
   - We search Qdrant for the most relevant chunks.
   - We send the question + those chunks to an LLM (e.g. Gemini) to generate an answer.
6. A Streamlit web app ties it all together into a simple UI.

Very short version:  
> “Ask a question → find relevant course pieces → generate a helpful answer.”

## 2. Prerequisites
Prerequisites (tools you need)

You don’t need to be a Docker/Tutor expert. You just need these installed:

1. **Git**  
   - So you can clone the repo and work with branches/PRs.

2. **Docker Desktop**   
   - This runs the servers for Open edX and Qdrant in containers.  
   - Download Docker Desktop from the official Docker website and install it like a normal app (Windows/Mac). https://www.docker.com/products/docker-desktop/

3. **uv (Python package/env manager)**  
   - We use `uv` instead of raw `pip` because it’s fast and simple once set up.

## 3. Setup - Getting the code on your machine
	1.	Go to the repo on GitHub and copy the clone URL (HTTPS is easiest).
	2.	In a terminal:
		```bash
		git clone <repo-url>
		cd openedx-tutor-rag
		```
    3. Create a virtual environment and activate it:
		```bash
		uv venv
		source .venv/bin/activate
		```
    4. Install dependencies:
		```bash
		uv sync
		```
    5. Every time you want to work on the project, activate the virtual environment:
		```bash
        cd <repo-name>
		source .venv/bin/activate
		```

## 4. Launching the Platform

Only do this if you have a Mac/Linux machine with 16GB RAM and are responsible for running Open edX.

1. Install the Qdrant Plugin: We need to tell Tutor where our custom plugin file is.

```bash
# 1. Ask Tutor where plugins live
DESTINATION=$(uv run tutor plugins printroot)

# 2. Link our file to that location
ln -s "$(pwd)/tutor-plugin/qdrant.py" "$DESTINATION/qdrant.py"

# 3. Enable it
uv run tutor plugins enable qdrant
```
2. Launch Open edX with Tutor:

### Option A: The Standard Way
By default, Tutor uses a special domain `local.overhang.io` that points to your computer. This usually works out of the box.

1. Configure Tutor (accepting defaults):
   ```bash
   uv run tutor config save --non-interactive
   ```
2. Launch the platform:
   ```bash
   uv run tutor local launch
   ```
   - Open edX will be at: **http://local.overhang.io**
   - Qdrant will be at: **http://localhost:6333/dashboard**

### Option B: The "Localhost" Workaround
If the URL above doesn't work (or you have DNS issues), you can force it to use `localhost`.

1. Configure Tutor to use localhost explicitly:
   ```bash
   uv run tutor config save --set LMS_HOST=localhost --set CMS_HOST=localhost
   ```
2. Launch the platform:
   ```bash
   uv run tutor local launch
   ```
   - Open edX will be at: **http://localhost**

## 5. Github Workflow (How to contribute)
Since we are a team, we never push directly to the main branch. We use "Feature Branches."

1. Start a New Task
Before you write any code, get the latest updates and create a new branch.
'''
Bash

# 1. Update your local project
git checkout main
git pull origin main

# 2. Create a new branch named after your task
# Example: git checkout -b feature/streamlit-ui
git checkout -b feature/<your-feature-name>
2. Save Your Work (Commit)
You did some coding. Now save it.
'''
'''
Bash

# See what files you changed
git status

# Add the files you want to save
git add .

# Save with a message (Be descriptive!)
git commit -m "Added the basic UI layout for the chat app"
3. Share Your Work (Push)
Send your branch to GitHub.
'''
'''
Bash

git push -u origin feature/<your-feature-name>
'''
4. Merge (Pull Request)
Go to our GitHub Repository.

You will see a yellow banner saying "feature/... had recent pushes".

Click "Compare & pull request".

Write a title and click Create Pull Request.

Wait for a teammate to review or approve, then click Merge.

Done! Now everyone else can pull your code into their main branch, and you can repeat from step 1 and open a new feature branch.

