# BlogPage – Blog Submission App with AI Agents

It combines a **frontend blog submission page** with **JavaScript validation** and an **agentic AI pipeline** (Planner → Reviewer → Finalizer) powered by a local LLM via Ollama.  
Deployment is supported using **Docker** and **AWS ECS**.

---

## 📖 Features

### Blog Page (Frontend)
- Clean and responsive **HTML/CSS blog form**
- **Form validation** using JavaScript:
  - All fields are required
  - Blog content must be at least 25 characters
  - User must accept terms & conditions
- Publishes blogs dynamically to the page after submission
- Tracks total number of successful submissions

### Agents (Python)
- **Planner Agent**: suggests initial tags and summary
- **Reviewer Agent**: reviews and refines the output
- **Finalizer Agent**: produces final JSON with tags, summary, and publish package
- Powered by **Ollama** running `llama3.2:3b` locally

### Deployment
- **Dockerfile** included to containerize the web app
- Can be deployed to **AWS ECS** using the Docker image

---

## 📂 Project Structure
```plaintext
.
├── Agents/
│   └── agents_talks.py       # Python script with AI agents
├── my-web-page/
│   ├── index.html            # Blog form page
│   ├── Fliq.js               # Validation + submission logic
│   ├── Dockerfile            # Container setup for the web app
│   └── .vscode/settings.json # Editor configuration
├── README.md                 # Project documentation
└── .DS_Store                 # System file (can be ignored)
