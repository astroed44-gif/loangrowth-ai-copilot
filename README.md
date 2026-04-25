# LoanGrowth AI Copilot

An agentic, multi-specialist performance marketing Copilot tailored for digital lending applications. 

## 🎯 Objective
Performance marketers at digital lending companies often optimize for shallow metrics (like Cost Per Install or Cost Per Registration) because downstream data (like loan approval rates, repayment rates, and default rates) is siloed. 

The **LoanGrowth AI Copilot** bridges this gap. It provides marketers with a conversational interface to query deep-funnel borrower quality, analyze creative effectiveness, and dynamically generate new ad copies based on patterns that actually yield high-quality, profitable borrowers.

## 📊 Data Schema
The copilot operates over a unified data model that connects top-of-funnel ad spend to bottom-of-funnel loan repayments. The underlying tables include:

1. **Daily Spend (`daily_spend`)**: Contains daily advertising metrics including impressions, clicks, installs, and spend across platforms (Meta, Google).
2. **Attribution (`attribution`)**: Maps ad engagements to specific `user_id`s, acting as the bridge between ad platforms and the product funnel.
3. **Onboarding (`onboarding`)**: Tracks the user's progression through the KYC (Know Your Customer) funnel.
4. **Loan Outcomes (`loan_outcomes`)**: Records whether a user's loan application was approved, rejected, and successfully disbursed.
5. **Repayment (`repayment`)**: Tracks the ultimate profitability metric—whether the borrower successfully repaid the loan or defaulted.
6. **Creative Library (`creative_library`)**: A taxonomy of the actual ad assets, including copy angles, visual hooks, urgency indicators, and trust signals.

## 🧠 Architecture
The application is built on a **Flask + Vanilla JS** stack, powered by **LangChain** and **OpenAI (GPT-4o)** using a multi-agent orchestration pattern.

### 1. The Multi-Agent Pipeline
When a user asks a question, it flows through a strict, 3-layer agentic architecture:

```mermaid
flowchart TD
    User(["💬 User Query<br><small><i>Natural language question</i></small>"]) --> Router{"🔀 Router Agent<br><small><i>Classifies intent & routes to specialists</i></small>"}
    
    Router -->|Intent: Funnel| A1["📊 Funnel Agent<br><small><i>Analyzes KYC drop-offs & conversion rates</i></small>"]
    Router -->|Intent: Creative| A2["🎨 Creative Agent<br><small><i>Finds winning visual hooks & ad angles</i></small>"]
    Router -->|Intent: Copies| A3["✍️ Copy Gen Agent<br><small><i>Generates 5 new high-converting ad copies</i></small>"]
    Router -->|Intent: Quality| A4["🏆 Borrower Quality Agent<br><small><i>Analyzes repayment, default, & approval rates</i></small>"]
    Router -->|Intent: Platform| A5["📱 Platform Agent<br><small><i>Compares Meta vs Google downstream CAC</i></small>"]
    
    A1 --> Sup["✨ Supervisor Agent<br><small><i>Synthesizes insights, formats evidence & sets decision</i></small>"]
    A2 --> Sup
    A3 --> Sup
    A4 --> Sup
    A5 --> Sup
    
    Sup --> UI(["🖥️ Frontend UI & Evidence Panel<br><small><i>Renders charts, tables, & generated copies</i></small>"])
```

- **Router Agent:** The traffic controller. It uses an LLM to analyze the user's intent alongside the conversation history (e.g., `COPY_GENERATION`, `PERFORMANCE`, `FUNNEL`). It then decides exactly which specialist agents need to be triggered to gather the required data.
- **Specialist Agents:** The data analysts. These are discrete, tool-equipped agents. Depending on the route, the specific agent runs Python/Pandas functions to slice the underlying data and generate localized insights:
  - *Funnel Agent*: Looks at where users drop off during the app onboarding process.
  - *Creative Agent*: Identifies which ad hooks and angles drive the highest quality users.
  - *Copy Gen Agent*: Uses the winning creative patterns to generate completely new, highly-targeted ad copies.
  - *Borrower Quality Agent*: Looks past the cost-per-install (CPI) to see if the acquired users actually repay their loans.
  - *Platform Agent*: Evaluates whether Meta or Google drives better downstream profitability.
- **Supervisor Agent:** The executive summarizer. It receives the raw analytical outputs from all the active specialists. It synthesizes this data into a strict JSON schema containing a definitive `decision`, the `why`, actionable `action_items`, and safely formats any generated ad copies to be rendered visually in the dynamic Evidence Panel.

### 2. Streaming & Memory
- **Memory Context:** The backend persists the latest 3 rounds of conversation (6 messages) as rolling context, allowing for natural follow-up questions.
- **Server-Sent Events (SSE):** The Flask backend uses SSE to stream the execution progress in real-time to the frontend (e.g., *"🔀 Routing your question..."* ➔ *"⚙️ Running copy_gen..."* ➔ *"✨ Synthesizing insights..."*), providing a highly responsive UX.

### 3. Frontend Presentation
- **Stateless UI:** The frontend acts as a thin client. It dynamically renders Markdown responses using `marked.js` and plots deep-funnel data using `Plotly.js`.
- **Dynamic Evidence Panel:** Alongside textual advice, the UI conditionally renders charts (Funnels, Bar charts) or tabular data (Winning Creatives, Copy Variants) based on the evidence type requested by the Supervisor.

---

## 🚀 Local Development

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
2. **Environment Variables:**
   Create a `.env` file in the root directory and add your OpenAI API key:
   ```env
   OPENAI_API_KEY=sk-your-api-key
   ```
3. **Run the server:**
   ```bash
   python3 app.py
   ```
4. **Access the application:**
   Navigate to `http://localhost:5000` in your web browser.
