## AI Assessment Generator: MCQ

This module is a self-contained script for generating Multiple Choice Question (MCQ) assessments based on provided lesson content. It uses a LangGraph state machine to loop and generate a specified number of unique questions, ensuring they are not simple repetitions.


## Features

Agentic Generation: Uses a LangGraph loop to generate one question at a time.

Repetition Avoidance: The state machine keeps track of already-generated questions and instructs the LLM not to repeat them.

Structured Output: Uses Google's JSON mode and Pydantic validation to ensure the LLM output is a perfectly structured MCQ object.

Rate Limit Handling: Includes a built-in time.sleep(65) to safely stay within the free tier API rate limits.

Modular & Testable: The script can be run directly for testing or imported as a module (mcq_graph) into your main application.

## Core Technologies

LangGraph (langgraph): For building the looping, stateful graph.

Google Generative AI (google-generativeai): To connect to and use the Gemini API.

Pydantic (pydantic): For strict data validation of the LLM's JSON output.

DotEnv (python-dotenv): For securely managing the Google API key.


##  Setup & Installation

This script is designed to be run from within a virtual environment.

1. Environment Setup

It is assumed you have already created and activated a virtual environment in the root scarlet_studio_backend folder.

```bash
python -m venv venv
```

For windows
```bash
.\venv\Scripts\avtivate
```

Form Mac
```bash
source venv/bin/activate
```


2. Install Dependencies

From your activated virtual environment, run the following command to install the necessary Python libraries:

```bash
pip install langgraph google-generativeai pydantic python-dotenv
```


3. Let Up API Key

This script requires a Google API key to function.

Create a file named .env inside this assesments folder.

Add your Google API key to this file, like so:
```bash
GOOGLE_API_KEY="your_api_key_here"
``` 


4. How to Run

This script can be run directly from the terminal for testing.

### Navigate to the folder:
Open your terminal and cd into this directory:

```bash
cd scarlet_studio_backend/ai_scripts/assesments
```


5. Run the script:
Make sure your lesson_content.txt file is present in this folder, then run:

```bash
python assessment.py
```