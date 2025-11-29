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
		```
		git clone <repo-url>
		cd openedx-tutor-rag
		```
    3. Create a virtual environment and activate it:
		```
		uv venv
		source .venv/bin/activate
		```
    4. Install dependencies:
		```
		uv sync
		```
    5. Every time you want to work on the project, activate the virtual environment:
		```
        cd <repo-name>
		source .venv/bin/activate
		```

## 4. Launching the Platform

Only do this if you have a Mac/Linux machine with 16GB RAM and are responsible for running Open edX.

1. Install the Qdrant Plugin: The plugin is created using the Tutor cookiecutter template and needs to be installed as a Python package.

```
# Install the plugin in development mode (from the qdrant_rag directory)
cd qdrant_rag
uv pip install -e .

# Enable the plugin
uv run tutor plugins enable qdrant
```

**Note:** The plugin structure `qdrant_rag/qdrant_rag/plugin.py` is correct for a Tutor cookiecutter plugin. The plugin is registered via the entry point `qdrant = "qdrant_rag.plugin"` in `pyproject.toml`, which Tutor will automatically discover once the package is installed.
2. Launch Open edX with Tutor:

### Option A: The Standard Way
By default, Tutor uses a special domain `local.overhang.io` that points to your computer. This usually works out of the box.

1. Configure Tutor (accepting defaults):
   ```
   uv run tutor config save --non-interactive
   ```
2. Launch the platform:
   ```
   uv run tutor local launch
   ```
   - Open edX will be at: **http://local.overhang.io**
   - Qdrant will be at: **http://localhost:6333/dashboard**

3. Stopping the Platform:
   To stop the containers without losing data:
   ```bash
   uv run tutor local stop
   ```

### Option B: The "Localhost" Workaround (If Option A fails)
If `local.overhang.io` doesn't work (e.g., due to DNS issues), use this method. It uses `*.localhost` domains which are automatically resolved by most browsers.

1. Configure Tutor to use `lms.localhost` and `studio.localhost`:
   ```bash
   uv run tutor config save --set LMS_HOST=lms.localhost --set CMS_HOST=studio.localhost
   ```
2. Launch the platform:
   ```bash
   uv run tutor local launch
   ```
   - Open edX will be at: **http://lms.localhost**
   - Studio will be at: **http://studio.localhost**
   - Qdrant will be at: **http://localhost:6333/dashboard**

## 5. Github Workflow (How to contribute)
Since we are a team, we never push directly to the main branch. We use "Feature Branches."

1. Start a New Task
Before you write any code, get the latest updates and create a new branch.
```


# 1. Update your local project
git checkout main
git pull origin main

# 2. Create a new branch named after your task
# Example: git checkout -b feature/streamlit-ui
git checkout -b feature/<your-feature-name>
```
2. Save Your Work (Commit)
You did some coding. Now save it.


```
# See what files you changed
git status

# Add the files you want to save
git add .

# Save with a message (Be descriptive!)
git commit -m "Added the basic UI layout for the chat app"
```

3. Share Your Work (Push)
Send your branch to GitHub.

```


git push -u origin feature/<your-feature-name>
```
4. Merge (Pull Request)
Go to our GitHub Repository.

You will see a yellow banner saying "feature/... had recent pushes".

Click "Compare & pull request".

Write a title and click Create Pull Request.

Wait for a teammate to review or approve, then click Merge.

Done! Now everyone else can pull your code into their main branch, and you can repeat from step 1 and open a new feature branch.

