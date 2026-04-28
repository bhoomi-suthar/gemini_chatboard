from google import genai
from config import GEMINI_API_KEY
import markdown

client = genai.Client(api_key=GEMINI_API_KEY)

SYSTEM_PROMPT = """You are a helpful, knowledgeable and professional AI assistant.

when answering questions:
- Give clear, accurate and well-structured responses
- Use bullet points or numbered lists when explaining multiple items
- Use bold text for important terms or headings
- Keep responses concise but complete — do not over-explain
- If a question has multiple parts, address each part separately
- If you don't know something, say so honestly instead of guessing

formatting rules:
- Always use proper markdown formatting
- Use headings for long responses to organize content
- Use code blocks when showing any code or commands
- Use examples where helpful to make concepts clearer

tone:
- Be professional but friendly
- Use natural greetings when appropriate.
- Do not use unnecessary filler phrases like "Great question!" or "Certainly!"
- Get straight to the point

what not to anser about:
- Harmful, offensive or inappropriate content
- Personal opinions on sensitive topics like politics, religion or race
- Illegal activities or anything that could cause harm
- Explicit or adult content of any kind

If asked about any of the above just politely say:
"I am not able to help with that. Please ask me something else."

response length:
- For simple questions give short answers (2-5 lines)
- For complex topics give detailed answers with sections
- Never give one word answers
- Always give at least one example for technical topics

when comparing things:
- Always use a table to show differences
- Include at least 3-4 comparison points
- End with a clear "Which is better?" recommendation

for coding questions:
- Always provide working code examples
- Add comments inside code to explain what each part does
- Mention which language/version the code is for
- Point out common mistakes or errors to avoid

"""


def get_gemini_response(user_message: str, mode: str = "table", chat_history: list = None) -> str:
    if chat_history is None:
        chat_history = []

    mode_instruction = ""
    chart_types = ["bar", "pie", "line", "doughnut", "radar"]

    if mode in chart_types:
        mode_instruction = f"""
IMPORTANT: If your response includes any comparison or tabular data, DO NOT use a markdown table.
Instead, represent the data as a Chart.js {mode} chart using a raw HTML <canvas> block like this:

<canvas id="chart1" width="400" height="260" style="width:400px;height:260px;max-width:100%"></canvas>
<script>
new Chart(document.getElementById('chart1'), {{
  type: '{mode}',
  data: {{
    labels: ['Label1', 'Label2', 'Label3'],
    datasets: [{{
      label: 'Comparison',
      data: [value1, value2, value3],
      backgroundColor: ['#4a90e2', '#e25c4a', '#2ecc71', '#f39c12', '#9b59b6'],
      borderColor: '#4a90e2'
    }}]
  }},
  options: {{ responsive: false, plugins: {{ legend: {{ display: true }} }} }}
}});
</script>

Use real data from your response in the chart. Only include a chart when data comparison is involved.
"""

    history_text = ""
    for msg in chat_history[-10:]:
        if msg["role"] == "user":
            history_text += f"User: {msg['text']}\n"
        elif msg["role"] == "ai":
            import re
            clean = re.sub(r'<[^>]+>', '', msg['text'])
            history_text += f"Assistant: {clean[:500]}\n"

    full_prompt = f"{SYSTEM_PROMPT}{mode_instruction}\n\n{history_text}User: {user_message}\nAssistant:"

    result = client.models.generate_content(
        model="gemini-3.1-flash-lite-preview",
        contents=full_prompt
    )

    return markdown.markdown(result.text, extensions=['fenced_code', 'codehilite', 'tables', 'nl2br'])



def generate_chat_title(user_message: str, ai_response: str) -> str:
    prompt = f"""Based on this conversation, generate a very short title (maximum 10 words, no punctuation, no quotes):

User: {user_message}
Assistant: {ai_response}

Title:"""
    try:
        result = client.models.generate_content(
            model="gemini-3.1-flash-lite-preview",
            contents=prompt
        )
        title = result.text.strip().strip('"').strip("'")
        return title[:40]
    except:
        return user_message[:30]


def check_topic_relevance(user_message: str, topic: str) -> bool:
    prompt = f"""Is the following user message related to the topic "{topic}"?

User message: "{user_message}"
Answer only YES or NO. Nothing else."""
    try:
        result = client.models.generate_content(
            model="gemini-3.1-flash-lite-preview",
            contents=prompt
        )
        answer = result.text.strip().upper()
        return "YES" in answer
    except:
        return True  # if check fails, allow message