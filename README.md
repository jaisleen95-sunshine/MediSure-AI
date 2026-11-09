
# 🧪 MediExplain AI

### Making Laboratory Reports Easier to Understand

**Team IdeaOrbit | GRAVITON 2026 | Open Innovation Theme**

## 📌 About the Project

MediExplain AI is an AI-powered web application designed to help users understand their laboratory reports in simple, clear language.

Medical reports often contain complex terminology, numerical values, and reference ranges that can be difficult to interpret. Our application simplifies this information and presents it in a structured, user-friendly format.

**Note:** MediExplain AI is an educational tool and does not provide medical diagnoses or treatment recommendations.

## 🎯 Problem Statement

Many people struggle to understand their laboratory reports due to unfamiliar medical terminology and complex numerical information.

Existing AI-based explanations may also lack consistency and make it difficult to verify results against the original report.

Our goal is to make laboratory reports easier to understand, review, and discuss with healthcare professionals.

## 💡 Our Solution

MediExplain AI allows users to:

- Upload laboratory reports in PDF or image format.
- Extract test names, values, units, and reference ranges.
- Review and correct extracted information.
- Identify whether values fall within the printed reference ranges.
- Receive simple, AI-generated explanations.
- View a structured summary of the report.
- Get suggested questions to discuss with a doctor.

## ⚙️ How It Works

1. **Upload Report:** The user uploads a PDF or image.
2. **Extract Data:** The application extracts laboratory test information.
3. **Verify Results:** The user reviews and confirms the extracted values.
4. **Compare Values:** Python compares confirmed values with the report's reference ranges.
5. **AI Explanation:** Gemini generates easy-to-understand explanations.
6. **View Results:** The application displays the results and summary in a structured format.

## 🛠️ Technology Stack

| Technology | Purpose |
|------------|---------|
| Python | Backend logic and data processing |
| Streamlit | Web application interface |
| Google Gemini API | AI-powered extraction and explanations |
| PyMuPDF | PDF text extraction |
| JSON | Structured data handling |
| HTML/CSS | Interface styling |

## 🚀 Installation and Setup

### 1. Clone the Repository

```bash
git clone <repository-url>
cd IdeaOrbit1
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Gemini API

Create a `.env` file in the project directory:

```env
GEMINI_API_KEY=your_api_key_here
GEMINI_MODEL=gemini-3.1-flash-lite
```

Never commit your `.env` file or API key to GitHub.

### 4. Run the Application

```bash
streamlit run app.py
```

Open the local URL displayed in your terminal.

## 👥 Meet Our Team

**Team Name:** IdeaOrbit

**Hackathon:** GRAVITON 2026

**Theme:** HealthTech

**Team Members:**
- Harshita — Team Leader
- Harneet
- Aditya
- Jaisleen

## 🔮 Future Scope

- Support for more laboratory report formats.
- Improved data extraction accuracy.
- Multilingual explanations.
- Stronger privacy and security measures.
- Medical expert review and validation.

## ⚠️ Disclaimer

MediExplain AI is an educational prototype.

It does not diagnose medical conditions, prescribe medication, or replace professional medical advice.

AI-generated explanations may contain errors. Users should verify their results and consult qualified healthcare professionals for medical decisions.

Uploaded report information is processed using the third-party Gemini API. Use fictional or appropriately de-identified reports for demonstrations.

---

**Developed by Team IdeaOrbit ❤️**

*GRAVITON 2026 — HealthTech*
