
import streamlit as st
import google.generativeai as genai
import io
import json
from datetime import date, datetime, timedelta

# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="AI Study Assistant",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown("""
<style>
    .main-title {
        font-size: 42px;
        font-weight: 700;
        margin-bottom: 5px;
    }

    .subtitle {
        font-size: 18px;
        color: #666;
        margin-bottom: 25px;
    }

    .feature-card {
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #ddd;
        margin-bottom: 15px;
    }

    .success-box {
        padding: 15px;
        border-radius: 10px;
        background-color: #e8f5e9;
        border: 1px solid #81c784;
    }

    .stat-card {
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #ddd;
        text-align: center;
    }

    .stat-number {
        font-size: 30px;
        font-weight: bold;
    }

    .small-text {
        color: #777;
        font-size: 14px;
    }
</style>
""", unsafe_allow_html=True)


# ============================================================
# API CONFIGURATION
# ============================================================

def get_api_key():
    """Get Gemini API key from Streamlit secrets."""

    try:
        return st.secrets["API_KEY"]
    except Exception:
        return None


API_KEY = get_api_key()

if API_KEY:
    genai.configure(api_key=API_KEY)

    # Gemini model
    model = genai.GenerativeModel("gemini-3.6-flash")
else:
    model = None


# ============================================================
# SESSION STATE
# ============================================================

if "messages" not in st.session_state:
    st.session_state.messages = []

if "quiz_data" not in st.session_state:
    st.session_state.quiz_data = []

if "quiz_score" not in st.session_state:
    st.session_state.quiz_score = 0

if "quiz_completed" not in st.session_state:
    st.session_state.quiz_completed = False

if "uploaded_text" not in st.session_state:
    st.session_state.uploaded_text = ""

if "uploaded_filename" not in st.session_state:
    st.session_state.uploaded_filename = ""

if "flashcards" not in st.session_state:
    st.session_state.flashcards = []

if "study_topics" not in st.session_state:
    st.session_state.study_topics = []

if "study_sessions" not in st.session_state:
    st.session_state.study_sessions = 0

if "quiz_history" not in st.session_state:
    st.session_state.quiz_history = []

if "recent_activity" not in st.session_state:
    st.session_state.recent_activity = []


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def call_ai(prompt, temperature=0.4):
    """
    Send a prompt to Gemini and return the response.
    """

    if not model:
        return (
            "⚠️ Gemini API key is missing.\n\n"
            "Please add your API key to Streamlit Secrets."
        )

    try:
        response = model.generate_content(
            prompt,
            generation_config={
                "temperature": temperature
            }
        )

        if response.text:
            return response.text

        return "The AI did not return a response."

    except Exception as e:
        return f"❌ AI request failed:\n\n{str(e)}"


def add_activity(activity):
    """Save an activity to recent activity."""

    st.session_state.recent_activity.insert(
        0,
        {
            "activity": activity,
            "time": datetime.now().strftime("%Y-%m-%d %H:%M")
        }
    )

    # Keep only latest 10 activities
    st.session_state.recent_activity = (
        st.session_state.recent_activity[:10]
    )


def extract_text_from_file(uploaded_file):
    """
    Extract text from TXT, PDF and DOCX files.
    """

    if uploaded_file is None:
        return ""

    file_type = uploaded_file.name.lower()

    try:

        # TXT
        if file_type.endswith(".txt"):
            return uploaded_file.read().decode("utf-8")

        # PDF
        elif file_type.endswith(".pdf"):
            import PyPDF2

            pdf_reader = PyPDF2.PdfReader(uploaded_file)

            text = ""

            for page in pdf_reader.pages:
                page_text = page.extract_text()

                if page_text:
                    text += page_text + "\n"

            return text

        # DOCX
        elif file_type.endswith(".docx"):
            from docx import Document

            document = Document(uploaded_file)

            text = ""

            for paragraph in document.paragraphs:
                text += paragraph.text + "\n"

            return text

        else:
            return ""

    except Exception as e:
        st.error(f"Could not read the file: {e}")
        return ""


def clean_json_response(text):
    """
    Remove markdown code fences if Gemini returns JSON inside them.
    """

    text = text.strip()

    if text.startswith("```json"):
        text = text[7:]

    elif text.startswith("```"):
        text = text[3:]

    if text.endswith("```"):
        text = text[:-3]

    return text.strip()


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.title("🎓 AI Study Assistant")

st.sidebar.markdown("---")

page = st.sidebar.radio(
    "Navigation",
    [
        "🏠 Dashboard",
        "🤖 AI Tutor",
        "📚 Notes Analyzer",
        "📝 Quiz Generator",
        "📖 Summarizer",
        "🎯 Exam Preparation",
        "🧠 Flashcards",
        "💻 Coding Tutor"
    ]
)

st.sidebar.markdown("---")

st.sidebar.info(
    "💡 Tip\n\n"
    "Upload your notes and use the AI to understand, "
    "summarize and practice them."
)

# ============================================================
# API WARNING
# ============================================================

if not API_KEY:
    st.warning(
        "⚠️ Gemini API key is not configured. "
        "AI features will not work until you add your API key."
    )


# ============================================================
# DASHBOARD
# ============================================================

if page == "🏠 Dashboard":

    st.markdown(
        '<div class="main-title">🎓 AI Study Assistant</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="subtitle">'
        'Your personal AI-powered study companion'
        '</div>',
        unsafe_allow_html=True
    )

    st.success(
        "Welcome! Study smarter, understand difficult topics, "
        "practice with quizzes and prepare for your exams."
    )

    st.markdown("## 🚀 Quick Actions")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "📝 Quizzes",
            len(st.session_state.quiz_history)
        )

    with col2:
        if st.session_state.quiz_history:
            avg = sum(
                q["percentage"]
                for q in st.session_state.quiz_history
            ) / len(st.session_state.quiz_history)
        else:
            avg = 0

        st.metric(
            "📊 Average Score",
            f"{avg:.0f}%"
        )

    with col3:
        st.metric(
            "📚 Topics",
            len(st.session_state.study_topics)
        )

    with col4:
        st.metric(
            "⏱️ Study Sessions",
            st.session_state.study_sessions
        )

    st.markdown("---")

    st.markdown("## ✨ Features")

    col1, col2 = st.columns(2)

    with col1:

        st.markdown("""
        ### 🤖 AI Tutor

        Ask questions and get simple explanations,
        examples and step-by-step solutions.
        """)

        st.markdown("""
        ### 📚 Notes Analyzer

        Upload PDF, TXT or DOCX notes and ask
        questions about your study material.
        """)

        st.markdown("""
        ### 📝 Quiz Generator

        Generate practice quizzes from your
        topics or uploaded notes.
        """)

        st.markdown("""
        ### 📖 Summarizer

        Convert long study material into
        useful exam-focused notes.
        """)

    with col2:

        st.markdown("""
        ### 🎯 Exam Preparation

        Generate a personalized study schedule
        based on your exam date.
        """)

        st.markdown("""
        ### 🧠 Flashcards

        Turn your notes into question-and-answer
        flashcards for quick revision.
        """)

        st.markdown("""
        ### 💻 Coding Tutor

        Understand code, find errors and learn
        programming concepts.
        """)

    st.markdown("---")

    st.markdown("## 🕒 Recent Activity")

    if st.session_state.recent_activity:

        for item in st.session_state.recent_activity[:5]:

            st.write(
                f"**{item['activity']}** — "
                f"{item['time']}"
            )

    else:
        st.info("No activity yet. Start studying! 🚀")


# ============================================================
# AI TUTOR
# ============================================================

elif page == "🤖 AI Tutor":

    st.title("🤖 AI Tutor")

    st.write(
        "Ask the AI tutor anything about your studies."
    )

    col1, col2 = st.columns(2)

    with col1:

        level = st.selectbox(
            "Explanation Level",
            [
                "Beginner",
                "Intermediate",
                "Advanced"
            ]
        )

    with col2:

        answer_length = st.selectbox(
            "Answer Length",
            [
                "Short",
                "Medium",
                "Detailed"
            ]
        )

    # Display previous messages

    for message in st.session_state.messages:

        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    question = st.chat_input(
        "Ask your study question..."
    )

    if question:

        st.session_state.messages.append(
            {
                "role": "user",
                "content": question
            }
        )

        with st.chat_message("user"):
            st.markdown(question)

        prompt = f"""
You are an expert university AI tutor.

Student level: {level}
Requested answer length: {answer_length}

Student question:
{question}

Instructions:

1. Explain the answer clearly.
2. Use simple language when possible.
3. Give examples.
4. Break difficult concepts into steps.
5. If mathematics is involved, show the steps.
6. If programming is involved, provide correct code.
7. Do not unnecessarily make the answer complicated.
8. If the student seems confused, explain the concept from basics.
"""

        with st.chat_message("assistant"):

            with st.spinner("AI Tutor is thinking..."):

                answer = call_ai(prompt)

            st.markdown(answer)

        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": answer
            }
        )

        st.session_state.study_sessions += 1

        add_activity("Used AI Tutor")


# ============================================================
# NOTES ANALYZER
# ============================================================

elif page == "📚 Notes Analyzer":

    st.title("📚 Study Notes Analyzer")

    st.write(
        "Upload your notes and ask questions based specifically "
        "on the uploaded material."
    )

    uploaded_file = st.file_uploader(
        "Upload your study material",
        type=["pdf", "txt", "docx"]
    )

    if uploaded_file:

        if (
            st.session_state.uploaded_filename
            != uploaded_file.name
        ):

            text = extract_text_from_file(
                uploaded_file
            )

            if text:

                st.session_state.uploaded_text = text
                st.session_state.uploaded_filename = (
                    uploaded_file.name
                )

                st.success(
                    f"✅ {uploaded_file.name} uploaded successfully!"
                )

                st.info(
                    f"Extracted approximately "
                    f"{len(text.split())} words."
                )

                add_activity(
                    f"Uploaded {uploaded_file.name}"
                )

            else:
                st.error(
                    "Could not extract text from this file."
                )

    if st.session_state.uploaded_text:

        st.markdown("---")

        st.subheader(
            f"📄 {st.session_state.uploaded_filename}"
        )

        question = st.text_area(
            "Ask a question about your notes",
            placeholder="Example: What is a process?"
        )

        if st.button(
            "🔍 Analyze Notes",
            use_container_width=True
        ):

            if not question.strip():

                st.warning(
                    "Please enter a question."
                )

            else:

                # Limit context to avoid excessively large prompts
                notes_text = st.session_state.uploaded_text

                if len(notes_text) > 50000:
                    notes_text = notes_text[:50000]

                prompt = f"""
You are a university study assistant.

Answer the student's question ONLY using
the study material provided below.

If the answer is not found in the material,
say clearly:

"The answer was not found in the provided notes."

Do not invent information.

STUDY MATERIAL:
----------------
{notes_text}
----------------

STUDENT QUESTION:
{question}

Give a clear and educational answer.
"""

                with st.spinner(
                    "Analyzing your notes..."
                ):

                    answer = call_ai(prompt)

                st.markdown("### 🤖 AI Answer")

                st.markdown(answer)

                add_activity(
                    "Analyzed study notes"
                )

        with st.expander("👀 Preview Uploaded Text"):

            st.text(
                st.session_state.uploaded_text[:5000]
            )


# ============================================================
# QUIZ GENERATOR
# ============================================================

elif page == "📝 Quiz Generator":

    st.title("📝 AI Quiz Generator")

    source_type = st.radio(
        "Quiz Source",
        [
            "Enter a Topic",
            "Use Uploaded Notes"
        ],
        horizontal=True
    )

    topic = ""

    if source_type == "Enter a Topic":

        topic = st.text_input(
            "Enter topic",
            placeholder="Example: Operating Systems"
        )

    else:

        if st.session_state.uploaded_text:

            topic = st.session_state.uploaded_text

            st.success(
                f"Using notes: "
                f"{st.session_state.uploaded_filename}"
            )

        else:

            st.warning(
                "Please upload notes first from "
                "the Notes Analyzer."
            )

    col1, col2, col3 = st.columns(3)

    with col1:

        number_questions = st.selectbox(
            "Number of Questions",
            [5, 10, 15, 20]
        )

    with col2:

        difficulty = st.selectbox(
            "Difficulty",
            ["Easy", "Medium", "Hard"]
        )

    with col3:

        question_type = st.selectbox(
            "Question Type",
            [
                "MCQs",
                "True/False",
                "Short Questions"
            ]
        )

    if st.button(
        "🚀 Generate Quiz",
        use_container_width=True
    ):

        if not topic.strip():

            st.warning(
                "Please enter a topic or upload notes."
            )

        else:

            if len(topic) > 30000:
                topic = topic[:30000]

            if question_type == "MCQs":

                format_instruction = """
Return JSON only in this format:

[
  {
    "question": "Question here",
    "options": [
      "Option A",
      "Option B",
      "Option C",
      "Option D"
    ],
    "answer": "Option A",
    "explanation": "Explanation here"
  }
]
"""

            elif question_type == "True/False":

                format_instruction = """
Return JSON only in this format:

[
  {
    "question": "Statement here",
    "answer": "True",
    "explanation": "Explanation here"
  }
]
"""

            else:

                format_instruction = """
Return JSON only in this format:

[
  {
    "question": "Question here",
    "answer": "Correct answer here",
    "explanation": "Explanation here"
  }
]
"""

            prompt = f"""
You are an expert university quiz generator.

Create {number_questions} questions.

Difficulty:
{difficulty}

Question type:
{question_type}

Study material/topic:
{topic}

Rules:

1. Questions must be educational.
2. Avoid duplicate questions.
3. Make answers accurate.
4. Include explanations.
5. Follow the requested JSON format exactly.

{format_instruction}
"""

            with st.spinner(
                "Generating your quiz..."
            ):

                response = call_ai(
                    prompt,
                    temperature=0.2
                )

            try:

                cleaned = clean_json_response(
                    response
                )

                quiz = json.loads(cleaned)

                st.session_state.quiz_data = quiz
                st.session_state.quiz_completed = False

                st.success(
                    "✅ Quiz generated successfully!"
                )

            except Exception:

                st.error(
                    "The AI returned an invalid quiz format. "
                    "Please try generating the quiz again."
                )


    # Display quiz

    if st.session_state.quiz_data:

        st.markdown("---")

        st.subheader("📝 Your Quiz")

        answers = {}

        for i, question in enumerate(
            st.session_state.quiz_data
        ):

            st.markdown(
                f"### Question {i + 1}"
            )

            st.write(
                question["question"]
            )

            if question_type == "MCQs":

                options = question.get(
                    "options",
                    []
                )

                answers[i] = st.radio(
                    "Select your answer:",
                    options,
                    key=f"quiz_{i}"
                )

            elif question_type == "True/False":

                answers[i] = st.radio(
                    "Select your answer:",
                    ["True", "False"],
                    key=f"quiz_{i}"
                )

            else:

                answers[i] = st.text_input(
                    "Your answer:",
                    key=f"quiz_{i}"
                )

        if st.button(
            "✅ Submit Quiz",
            use_container_width=True
        ):

            score = 0

            results = []

            for i, question in enumerate(
                st.session_state.quiz_data
            ):

                correct = str(
                    question["answer"]
                ).strip().lower()

                user_answer = str(
                    answers.get(i, "")
                ).strip().lower()

                is_correct = (
                    user_answer == correct
                )

                if is_correct:
                    score += 1

                results.append(
                    {
                        "question":
                            question["question"],
                        "user_answer":
                            answers.get(i, ""),
                        "correct_answer":
                            question["answer"],
                        "correct":
                            is_correct,
                        "explanation":
                            question.get(
                                "explanation",
                                ""
                            )
                    }
                )

            total = len(
                st.session_state.quiz_data
            )

            percentage = (
                score / total * 100
                if total > 0
                else 0
            )

            st.session_state.quiz_score = score
            st.session_state.quiz_completed = True

            st.session_state.quiz_history.append(
                {
                    "score": score,
                    "total": total,
                    "percentage": percentage,
                    "date":
                        datetime.now().strftime(
                            "%Y-%m-%d %H:%M"
                        )
                }
            )

            add_activity(
                f"Completed quiz: "
                f"{score}/{total}"
            )

            st.success(
                f"🎉 Your Score: "
                f"{score}/{total} "
                f"({percentage:.0f}%)"
            )

            st.markdown("### 📊 Results")

            for i, result in enumerate(results):

                if result["correct"]:

                    st.success(
                        f"Question {i + 1}: ✅ Correct"
                    )

                else:

                    st.error(
                        f"Question {i + 1}: ❌ Incorrect"
                    )

                    st.write(
                        f"**Your answer:** "
                        f"{result['user_answer']}"
                    )

                    st.write(
                        f"**Correct answer:** "
                        f"{result['correct_answer']}"
                    )

                    st.write(
                        f"**Explanation:** "
                        f"{result['explanation']}"
                    )


# ============================================================
# SUMMARIZER
# ============================================================

elif page == "📖 Summarizer":

    st.title("📖 AI Study Summarizer")

    st.write(
        "Turn long study material into simple "
        "exam-focused notes."
    )

    input_method = st.radio(
        "Choose input",
        [
            "Enter Text",
            "Use Uploaded Notes"
        ],
        horizontal=True
    )

    material = ""

    if input_method == "Enter Text":

        material = st.text_area(
            "Enter study material",
            height=300,
            placeholder="Paste your notes here..."
        )

    else:

        if st.session_state.uploaded_text:

            material = st.session_state.uploaded_text

            st.success(
                f"Using {st.session_state.uploaded_filename}"
            )

        else:

            st.warning(
                "Please upload notes first."
            )

    summary_type = st.selectbox(
        "Summary Type",
        [
            "Short Summary",
            "Detailed Summary",
            "Exam-Focused Notes"
        ]
    )

    if st.button(
        "📖 Generate Summary",
        use_container_width=True
    ):

        if not material.strip():

            st.warning(
                "Please provide study material."
            )

        else:

            if len(material) > 40000:
                material = material[:40000]

            prompt = f"""
You are an expert university study assistant.

Create a {summary_type} from the following
study material.

Include useful information such as:

- Main concepts
- Important points
- Definitions
- Examples
- Formulas when present
- Exam-focused information

Use clear headings and bullet points.

STUDY MATERIAL:

{material}
"""

            with st.spinner(
                "Creating summary..."
            ):

                summary = call_ai(prompt)

            st.markdown("### 📚 Summary")

            st.markdown(summary)

            add_activity(
                "Generated study summary"
            )


# ============================================================
# EXAM PREPARATION
# ============================================================

elif page == "🎯 Exam Preparation":

    st.title("🎯 Exam Preparation Planner")

    st.write(
        "Create a personalized study plan based on "
        "your exam date and available study time."
    )

    subject = st.text_input(
        "Subject",
        placeholder="Example: Information Security"
    )

    topics = st.text_area(
        "Topics",
        placeholder=(
            "Example:\n"
            "CIA Triad\n"
            "Caesar Cipher\n"
            "Playfair Cipher\n"
            "Vigenere Cipher"
        )
    )

    exam_date = st.date_input(
        "Exam Date",
        min_value=date.today()
    )

    study_hours = st.number_input(
        "Available study hours per day",
        min_value=1.0,
        max_value=12.0,
        value=3.0,
        step=0.5
    )

    if st.button(
        "🎯 Create Study Plan",
        use_container_width=True
    ):

        if not subject.strip():

            st.warning(
                "Please enter the subject."
            )

        elif not topics.strip():

            st.warning(
                "Please enter your topics."
            )

        else:

            days_remaining = (
                exam_date - date.today()
            ).days

            prompt = f"""
You are an expert academic study planner.

Create a realistic exam preparation plan.

Subject:
{subject}

Topics:
{topics}

Exam date:
{exam_date}

Days remaining:
{days_remaining}

Available study hours per day:
{study_hours}

Create a day-by-day study plan.

Include:

1. Topics to study
2. Revision
3. Practice questions
4. Quiz sessions
5. Difficult-topic revision
6. Final revision before the exam

Keep the plan realistic for a university student.
"""

            with st.spinner(
                "Creating your study plan..."
            ):

                plan = call_ai(prompt)

            st.markdown("### 📅 Your Study Plan")

            st.markdown(plan)

            add_activity(
                f"Created exam plan for {subject}"
            )


# ============================================================
# FLASHCARDS
# ============================================================

elif page == "🧠 Flashcards":

    st.title("🧠 AI Flashcard Generator")

    st.write(
        "Generate flashcards for quick revision."
    )

    source = st.radio(
        "Source",
        [
            "Topic",
            "Uploaded Notes"
        ],
        horizontal=True
    )

    flashcard_source = ""

    if source == "Topic":

        flashcard_source = st.text_input(
            "Enter topic",
            placeholder="Example: Computer Networks"
        )

    else:

        if st.session_state.uploaded_text:

            flashcard_source = (
                st.session_state.uploaded_text
            )

            st.success(
                f"Using {st.session_state.uploaded_filename}"
            )

        else:

            st.warning(
                "Please upload notes first."
            )

    number_cards = st.selectbox(
        "Number of flashcards",
        [5, 10, 15, 20]
    )

    if st.button(
        "🧠 Generate Flashcards",
        use_container_width=True
    ):

        if not flashcard_source.strip():

            st.warning(
                "Please enter a topic or upload notes."
            )

        else:

            if len(flashcard_source) > 30000:
                flashcard_source = (
                    flashcard_source[:30000]
                )

            prompt = f"""
Create {number_cards} educational flashcards.

Topic/study material:

{flashcard_source}

Return JSON only:

[
  {{
    "question": "Question",
    "answer": "Answer"
  }}
]

Rules:

- Questions should test important concepts.
- Answers should be accurate.
- Keep answers concise.
- Avoid duplicate questions.
"""

            with st.spinner(
                "Creating flashcards..."
            ):

                response = call_ai(
                    prompt,
                    temperature=0.2
                )

            try:

                cleaned = clean_json_response(
                    response
                )

                flashcards = json.loads(
                    cleaned
                )

                st.session_state.flashcards = (
                    flashcards
                )

                st.success(
                    "✅ Flashcards generated!"
                )

            except Exception:

                st.error(
                    "Could not create flashcards. "
                    "Please try again."
                )

    # Display flashcards

    if st.session_state.flashcards:

        st.markdown("---")

        st.subheader("🧠 Your Flashcards")

        for i, card in enumerate(
            st.session_state.flashcards
        ):

            with st.expander(
                f"Card {i + 1}: "
                f"{card['question']}"
            ):

                st.write(
                    f"**Answer:** "
                    f"{card['answer']}"
                )


# ============================================================
# CODING TUTOR
# ============================================================

elif page == "💻 Coding Tutor":

    st.title("💻 AI Coding Tutor")

    st.write(
        "Learn programming, understand code and "
        "find programming errors."
    )

    language = st.selectbox(
        "Programming Language",
        [
            "Python",
            "JavaScript",
            "C++",
            "Java"
        ]
    )

    task = st.selectbox(
        "What do you want help with?",
        [
            "Explain Code",
            "Find Errors",
            "Improve Code",
            "Solve Programming Problem",
            "Teach Me a Concept"
        ]
    )

    code_or_question = st.text_area(
        "Enter your code or question",
        height=300,
        placeholder=(
            "Example:\n"
            "for i in range(5):\n"
            "    print(i)"
        )
    )

    if st.button(
        "💻 Analyze",
        use_container_width=True
    ):

        if not code_or_question.strip():

            st.warning(
                "Please enter code or a question."
            )

        else:

            prompt = f"""
You are an expert programming tutor.

Programming language:
{language}

Student wants:
{task}

Student input:

{code_or_question}

Instructions:

1. Explain the answer in simple language.
2. If there is an error, identify it.
3. Explain why the error happens.
4. Provide corrected code when necessary.
5. Explain the correction.
6. Give a simple example.
7. Help the student learn instead of simply giving an answer.
"""

            with st.spinner(
                "Analyzing your code..."
            ):

                answer = call_ai(prompt)

            st.markdown("### 🤖 Coding Tutor")

            st.markdown(answer)

            add_activity(
                "Used Coding Tutor"
            )
