# 📁 Project Folder Structure

Complete folder structure for EduCurate - Personalised Learning Assistant

```
Personalised-Learning-Assistant-main/
│
├── .gitattributes
├── .gitignore
├── README.md
│
├── Backend/
│   ├── .env                          # ⚠️ Should be in .gitignore
│   ├── __pycache__/                  # ⚠️ Should be in .gitignore
│   ├── *.pyc, *.pyo, *.pyd           # ⚠️ Should be in .gitignore
│   │
│   ├── aes_server.py
│   ├── audio.wav                     # ⚠️ Generated file - consider ignoring
│   ├── auto_eval_client.py
│   ├── bloom_questions.txt           # ⚠️ Generated file - consider ignoring
│   ├── bloom_questions_unique.txt    # ⚠️ Generated file - consider ignoring
│   ├── database.py
│   ├── dist_metrics.pxd
│   ├── main.py
│   ├── models.py
│   ├── pyproject.toml
│   ├── requirements.txt
│   ├── schemas.py
│   ├── testimport.py
│   ├── transcript.txt                # ⚠️ Generated file - consider ignoring
│   ├── utils.py
│   │
│   ├── jobs/                         # ⚠️ Generated job files - consider ignoring
│   │   └── *.json                    # Job status files
│   │
│   ├── Auto_Eval/
│   │   ├── .env                      # ⚠️ Should be in .gitignore
│   │   ├── .DS_Store                 # ⚠️ macOS system file
│   │   ├── .python-version
│   │   ├── pyproject.toml
│   │   ├── README.md
│   │   ├── run_server.py
│   │   ├── server.py
│   │   ├── verify_setup.py
│   │   │
│   │   └── src/
│   │       ├── .DS_Store             # ⚠️ macOS system file
│   │       ├── auto_eval/
│   │       │   ├── __pycache__/      # ⚠️ Should be in .gitignore
│   │       │   ├── __init__.py
│   │       │   │
│   │       │   ├── agents/
│   │       │   │   ├── __pycache__/  # ⚠️ Should be in .gitignore
│   │       │   │   ├── __init__.py
│   │       │   │   ├── aggregator.py
│   │       │   │   ├── evaluator.py
│   │       │   │   ├── model_generator.py
│   │       │   │   ├── reflector.py
│   │       │   │   ├── retriever.py
│   │       │   │   └── rubric_generator.py
│   │       │   │
│   │       │   ├── core/
│   │       │   │   ├── __pycache__/  # ⚠️ Should be in .gitignore
│   │       │   │   ├── __init__.py
│   │       │   │   ├── config.py
│   │       │   │   └── types.py
│   │       │   │
│   │       │   ├── pipeline/
│   │       │   │   ├── __pycache__/  # ⚠️ Should be in .gitignore
│   │       │   │   ├── __init__.py
│   │       │   │   ├── cli.py
│   │       │   │   └── graph.py
│   │       │   │
│   │       │   └── server/
│   │       │       ├── __pycache__/  # ⚠️ Should be in .gitignore
│   │       │       ├── __init__.py
│   │       │       └── mcp_server.py
│   │       │
│   │       └── auto_eval.egg-info/   # ⚠️ Should be in .gitignore
│   │           ├── dependency_links.txt
│   │           ├── entry_points.txt
│   │           ├── PKG-INFO
│   │           ├── requires.txt
│   │           ├── SOURCES.txt
│   │           └── top_level.txt
│   │
│   ├── Question_Generation/
│   │   ├── __pycache__/              # ⚠️ Should be in .gitignore
│   │   ├── __init__.py
│   │   ├── bloom_from_transcript.py
│   │   ├── bloom_qg_bert_advanced.py
│   │   ├── lecture_asr_pipeline_1.py
│   │   ├── transcript.py
│   │   └── updated_bloom_dynamic_questions.py
│   │
│   ├── RoadmapGeneration/
│   │   ├── __pycache__/              # ⚠️ Should be in .gitignore
│   │   ├── ModelFineTune.py
│   │   │
│   │   └── agents/
│   │       ├── __pycache__/          # ⚠️ Should be in .gitignore
│   │       ├── difficulty_estimator.py
│   │       ├── personalizer_agent.py
│   │       ├── prerequisite_inference.py
│   │       ├── topic_decomposer.py
│   │       └── validator_agent.py
│   │
│   └── routes/
│       ├── __pycache__/              # ⚠️ Should be in .gitignore
│       ├── evaluation.py
│       └── roadmap.py
│
└── Frontend/
    ├── .eslintrc.json
    ├── .gitignore
    ├── components.json
    ├── favicon.ico
    ├── next.config.js
    ├── package-lock.json
    ├── package.json
    ├── postcss.config.js
    ├── README.md
    ├── tailwind.config.ts
    ├── tsconfig.json
    │
    ├── node_modules/                 # ⚠️ Should be in .gitignore
    ├── .next/                        # ⚠️ Next.js build folder - should be in .gitignore
    │
    ├── app/
    │   ├── globals.css
    │   ├── layout.tsx
    │   ├── page.tsx
    │   │
    │   ├── course/
    │   │   ├── layout.tsx
    │   │   ├── page.tsx
    │   │   │
    │   │   ├── test/
    │   │   │   ├── page.tsx
    │   │   │   └── results/
    │   │   │       └── page.tsx
    │   │   │
    │   │   └── videos/
    │   │       ├── page.tsx
    │   │       └── watch/
    │   │           └── page.tsx
    │   │
    │   ├── login/
    │   │   ├── page.tsx
    │   │   └── password-reset/
    │   │       └── page.tsx
    │   │
    │   ├── sign-in/
    │   │   └── page.tsx
    │   │
    │   └── user-info/
    │       ├── layout.tsx
    │       └── page.tsx
    │
    ├── components/
    │   ├── HomePage.tsx
    │   ├── LottieAnimation.tsx
    │   ├── RoadmapAnimation.tsx
    │   │
    │   ├── intro/
    │   │   ├── BookModel.tsx
    │   │   ├── IntroScene.tsx
    │   │   └── MysticalBook.tsx
    │   │
    │   ├── learn_content/
    │   │   ├── DisplayScores.tsx
    │   │   ├── TestLandingPage.tsx
    │   │   └── VideoLandingPage.tsx
    │   │
    │   ├── search/
    │   │   ├── CourseVideos.tsx
    │   │   ├── Home.tsx
    │   │   ├── SearchFilters.tsx
    │   │   ├── SearchResults.tsx
    │   │   └── VideoSearch.tsx
    │   │
    │   ├── sign-up/
    │   │   ├── ForgotPassword.tsx
    │   │   ├── Login.tsx
    │   │   └── SignUp.tsx
    │   │
    │   ├── ui/                       # 58 UI component files (.tsx)
    │   │   ├── 3d-card.tsx
    │   │   ├── accordion.tsx
    │   │   ├── alert-dialog.tsx
    │   │   ├── alert.tsx
    │   │   ├── aspect-ratio.tsx
    │   │   ├── aurora-background.tsx
    │   │   ├── avatar.tsx
    │   │   ├── background-beams-with-collision.tsx
    │   │   ├── background-boxes.tsx
    │   │   ├── badge.tsx
    │   │   ├── breadcrumb.tsx
    │   │   ├── button.tsx
    │   │   ├── calendar.tsx
    │   │   ├── canvas-reveal-effect.tsx
    │   │   ├── card.tsx
    │   │   ├── carousel.tsx
    │   │   ├── chart.tsx
    │   │   ├── checkbox.tsx
    │   │   ├── collapsible.tsx
    │   │   ├── command.tsx
    │   │   ├── context-menu.tsx
    │   │   ├── dialog.tsx
    │   │   ├── drawer.tsx
    │   │   ├── dropdown-menu.tsx
    │   │   ├── file-upload.tsx
    │   │   ├── form.tsx
    │   │   ├── grid.tsx
    │   │   ├── hover-card.tsx
    │   │   ├── input-otp.tsx
    │   │   ├── input.tsx
    │   │   ├── label.tsx
    │   │   ├── lamp.tsx
    │   │   ├── menubar.tsx
    │   │   ├── navigation-menu.tsx
    │   │   ├── pagination.tsx
    │   │   ├── popover.tsx
    │   │   ├── progress.tsx
    │   │   ├── radio-group.tsx
    │   │   ├── resizable.tsx
    │   │   ├── scroll-area.tsx
    │   │   ├── select.tsx
    │   │   ├── separator.tsx
    │   │   ├── sheet.tsx
    │   │   ├── sidebar.tsx
    │   │   ├── skeleton.tsx
    │   │   ├── slider.tsx
    │   │   ├── sonner.tsx
    │   │   ├── switch.tsx
    │   │   ├── table.tsx
    │   │   ├── tabs.tsx
    │   │   ├── text-generate-effect.tsx
    │   │   ├── textarea.tsx
    │   │   ├── toast.tsx
    │   │   ├── toaster.tsx
    │   │   ├── toggle-group.tsx
    │   │   ├── toggle.tsx
    │   │   ├── tooltip.tsx
    │   │   └── typewriter-effect.tsx
    │   │
    │   └── video/
    │       ├── VideoCard.tsx
    │       └── VideoModal.tsx
    │
    ├── hooks/
    │   └── use-toast.ts
    │
    ├── lib/
    │   ├── utils.ts
    │   └── youtube-api.ts
    │
    ├── public/
    │   └── models/
    │       ├── 1238619762_old-book-textures6.jpg
    │       ├── 138553362.jpg
    │       ├── archibase.net.txt
    │       ├── Book old N051113.3DS
    │       ├── Book old N051113.gsm
    │       ├── brown.jpg
    │       └── paper.jpg
    │
    └── types/
        └── video.ts
```

## 📝 Key File Types and Patterns

### Python Files
- `*.py` - Python source files
- `*.pyc`, `*.pyo`, `*.pyd` - Compiled Python files (should ignore)
- `__pycache__/` - Python cache directories (should ignore)
- `*.egg-info/` - Python package metadata (should ignore)
- `.venv/`, `venv/`, `env/` - Virtual environments (should ignore)

### Node.js/Next.js Files
- `node_modules/` - npm packages (should ignore)
- `.next/` - Next.js build output (should ignore)
- `package-lock.json` - Lock file (usually committed)
- `*.tsx`, `*.ts` - TypeScript files

### Configuration Files
- `.env`, `*.env` - Environment variables (should ignore)
- `*.toml` - TOML config files
- `*.json` - JSON config files
- `*.config.js` - Config files

### Generated/Runtime Files
- `*.wav`, `*.mp3`, `*.mp4` - Audio/video files (consider ignoring)
- `*.txt` - Text files (some generated, some source)
- `jobs/*.json` - Job status files (consider ignoring)
- `*.log` - Log files (should ignore)

### System Files
- `.DS_Store` - macOS Finder metadata (should ignore)
- `Thumbs.db` - Windows thumbnail cache (should ignore)
- `.python-version` - Python version file (usually committed)

### Build/Dist Files
- `dist/`, `build/` - Build output directories (should ignore)
- `*.pid` - Process ID files (should ignore)

## ⚠️ Files/Directories That Should Be Ignored

1. **Environment files**: `.env`, `*.env`
2. **Python cache**: `__pycache__/`, `*.pyc`, `*.pyo`, `*.pyd`
3. **Virtual environments**: `.venv/`, `venv/`, `env/`
4. **Node modules**: `node_modules/`
5. **Build outputs**: `.next/`, `dist/`, `build/`
6. **System files**: `.DS_Store`, `Thumbs.db`
7. **Log files**: `*.log`, `logs/`
8. **Generated files**: `*.egg-info/`, job JSON files (consider)
9. **IDE files**: `.vscode/`, `.idea/`, `.history/`
10. **Large media files**: Consider ignoring `.wav`, `.mp4` if auto-generated


