# 204203_GROUP2

# 🍳 ChefBot - AI Cooking Assistant

ผู้ช่วยพ่อครัวอัจฉริยะที่ใช้ AI ช่วยแนะนำสูตรอาหาร ค้นหาข้อมูลโภชนาการ และวิเคราะห์วัตถุดิบจากรูปภาพ

![ChefBot Banner](https://img.freepik.com/premium-photo/cute-robot-chef_996086-13554.jpg)

## ✨ Features

### 🎯 Core Features
- 💬 **AI Chatbot** - คุยกับ AI เพื่อขอคำแนะนำในการทำอาหาร
- 🔍 **Web Search** - ค้นหาข้อมูลสูตรอาหารและเทคนิคการทำอาหารจากอินเทอร์เน็ต
- 🍽️ **Recipe Search** - ค้นหาสูตรอาหารจากวัตถุดิบที่มี (Spoonacular API)
- 📊 **Nutrition Info** - ดูข้อมูลโภชนาการของวัตถุดิบ (USDA Database)
- 📸 **Vision AI** - อัปโหลดรูปภาพเพื่อตรวจจับวัตถุดิบอัตโนมัติ (GPT-4o)

### 🎨 UI/UX Features
- 🎨 Beautiful gradient UI with smooth animations
- 📜 Chat history with easy navigation
- ⚙️ Customizable AI settings (model, temperature)
- 📱 Responsive design for all devices
- 🔄 Multi-turn conversation support

### 🤖 Supported AI Models
- **GPT-4o Mini** (Default) - Fast, cost-effective, supports vision
- **GPT-4o** - Most capable OpenAI model
- **GPT-4 Turbo** - Balanced performance
- **Llama 3.3 70B** (Groq) - Fast inference
- **Mixtral 8x7B** (Groq) - Efficient multi-expert model

## 📁 Project Structure
chefbot/
├── app.py                  # Main application entry point
├── config.py               # Configuration & constants
├── helpers.py              # Helper functions (session state, validation)
├── tools_executor.py       # Tool execution logic
├── ai_handler.py           # AI response generation
├── ui_components.py        # UI styling & reusable components
├── vision_handler.py       # Vision AI integration
├── cook_tool.py            # Cooking/recipe tools
├── search_tools.py         # Web search tools
├── prompts.py              # System prompts
│
├── utils/                  # Vision utilities
│   ├── init.py
│   ├── llm_client.py       # LLM client wrapper
│   └── vision.py           # Image processing utilities
│
├── pages/                  # Page components
│   ├── init.py
│   ├── home.py             # Home page with image upload
│   └── chat.py             # Chat interface
│
├── .env                    # Environment variables (create this)
├── requirements.txt        # Python dependencies
└── README.md              # This file

