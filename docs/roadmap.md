# TempoAI Development Roadmap

## Project Goal

Build and deploy a polished AI-powered golf swing analysis platform that demonstrates full-stack development, computer vision, video processing, explainable swing analysis, and generative AI integration.

TempoAI is a portfolio project. It will not include payments, subscriptions, or commercial billing features.

---

## Milestone 1: Product Planning

### Tasks

* Define product requirements
* Define system architecture
* Define UI and user experience
* Define development roadmap
* Create initial README
* Configure `.gitignore`
* Push planning documentation to GitHub

### Completion Criteria

* All planning documents are complete
* Repository structure is organized
* Project scope is clearly defined
* GitHub repository is up to date

### Planned Commits

```text
docs: add initial project structure and product requirements
docs: define system architecture
docs: define application UI and user experience
docs: add development roadmap
docs: create initial project README
```

---

## Milestone 2: Project Foundation

### Tasks

* Initialize React, TypeScript, and Vite frontend
* Install and configure Tailwind CSS
* Configure React Router
* Install Framer Motion and Lucide React
* Initialize Express and TypeScript backend
* Configure development scripts
* Add centralized backend error handling
* Add environment variable support
* Create backend health endpoint
* Connect frontend to backend health endpoint
* Configure ESLint and formatting
* Confirm frontend and backend builds

### Completion Criteria

* Frontend runs locally
* Backend runs locally
* Frontend successfully calls the backend
* Both projects build without errors

### Branch

```text
feature/project-foundation
```

### Planned Commits

```text
chore: initialize React TypeScript frontend
chore: configure Tailwind and frontend dependencies
chore: initialize Express TypeScript backend
feat: add backend health endpoint
feat: connect frontend to backend health check
chore: configure project linting and environment files
```

---

## Milestone 3: Design System and Application Shell

### Tasks

* Define color tokens and typography
* Create reusable buttons, inputs, cards, and badges
* Build desktop sidebar
* Build mobile navigation
* Create responsive application shell
* Add page transitions
* Add loading skeletons and empty states
* Create placeholder routes

### Pages

* Dashboard
* New Analysis
* Swing History
* Compare Swings
* Profile
* Login
* Register

### Completion Criteria

* Navigation works across all routes
* Layout is responsive
* Shared components are reusable
* Application has a polished sports-tech identity

### Branch

```text
feature/design-system
```

### Planned Commits

```text
feat: define TempoAI design system
feat: create reusable interface components
feat: build responsive application shell
feat: add navigation and placeholder routes
feat: add page transitions and loading states
```

---

## Milestone 4: Mock Product Experience

### Tasks

* Build dashboard using mock data
* Build new analysis upload interface
* Build processing screen
* Build analysis results interface
* Build swing history interface
* Build comparison interface
* Add mock charts and metrics
* Add mock coaching findings and drills

### Completion Criteria

* Recruiters can navigate a complete visual product
* Every major page exists
* Desktop and mobile layouts are polished
* Mock data closely resembles final application data

### Branch

```text
feature/mock-product
```

### Planned Commits

```text
feat: build mock performance dashboard
feat: create swing upload experience
feat: add swing processing interface
feat: build mock swing analysis results
feat: create swing history experience
feat: add side-by-side swing comparison
```

---

## Milestone 5: Database and Authentication

### Tasks

* Create Neon PostgreSQL database
* Configure Prisma ORM
* Create User and SwingAnalysis models
* Add database migrations
* Implement registration
* Implement login
* Implement JWT authentication
* Implement password hashing
* Add authenticated user endpoint
* Create frontend authentication context
* Add protected routes
* Add logout and session restoration

### Completion Criteria

* Users can register and log in
* Passwords are securely hashed
* Protected routes require authentication
* Sessions persist after page refresh
* Users can log out successfully

### Branch

```text
feature/authentication
```

### Planned Commits

```text
chore: configure Prisma and PostgreSQL
feat: create user and swing analysis database models
feat: implement registration and login endpoints
feat: add JWT authentication middleware
feat: connect frontend authentication flow
feat: protect application routes and restore sessions
```

---

## Milestone 6: Video Uploads

### Tasks

* Configure Cloudinary
* Create secure upload configuration
* Build video file validation
* Validate file format
* Validate video duration
* Validate file size
* Add browser video preview
* Upload video directly to Cloudinary
* Save video metadata to PostgreSQL
* Display uploaded swings in history

### Completion Criteria

* Users can upload supported videos
* Invalid videos are rejected clearly
* Upload progress is visible
* Uploaded swings persist in the database
* Users only see their own uploads

### Branch

```text
feature/video-upload
```

### Planned Commits

```text
chore: configure Cloudinary video storage
feat: add golf swing video validation
feat: create video preview and upload progress
feat: upload swing videos directly to Cloudinary
feat: persist uploaded swing metadata
feat: display user swing uploads in history
```

---

## Milestone 7: Video Analysis Player

### Tasks

* Build custom video player controls
* Add frame stepping
* Add playback speed controls
* Add timeline scrubbing
* Add fullscreen support
* Create canvas overlay
* Add skeleton visibility toggle
* Add measurement visibility toggle
* Add manual swing phase markers

### Completion Criteria

* Users can inspect a swing frame by frame
* Controls work on desktop and mobile
* Canvas remains aligned with the video
* Manual phase markers can move the video to selected timestamps

### Branch

```text
feature/video-player
```

### Planned Commits

```text
feat: build custom swing video player
feat: add slow motion and frame controls
feat: create synchronized canvas overlay
feat: add manual swing phase navigation
```

---

## Milestone 8: MediaPipe Pose Detection

### Tasks

* Install MediaPipe Tasks Vision
* Load Pose Landmarker
* Analyze sampled video frames
* Capture landmark confidence
* Draw skeleton connections
* Normalize landmark data
* Handle low-confidence frames
* Add processing progress
* Store pose results

### Completion Criteria

* A skeleton appears over the golfer
* Pose processing does not freeze the interface
* Low-confidence results are handled safely
* Landmark data is saved for later analysis

### Branch

```text
feature/pose-detection
```

### Planned Commits

```text
chore: configure MediaPipe Pose Landmarker
feat: process sampled golf swing video frames
feat: render pose landmarks over video
feat: handle low-confidence pose detection
feat: persist processed landmark data
```

---

## Milestone 9: Swing Phase Detection

### Tasks

* Detect address
* Detect takeaway
* Detect top of backswing
* Detect downswing transition
* Estimate impact
* Detect finish
* Assign confidence values
* Allow manual corrections
* Create camera-angle-specific heuristics

### Completion Criteria

* Major swing phases are detected automatically
* Users can correct incorrect markers
* Face-on and down-the-line videos use appropriate logic
* Low-confidence phases are clearly labeled

### Branch

```text
feature/swing-phases
```

### Planned Commits

```text
feat: detect address and takeaway positions
feat: identify top and downswing transition
feat: estimate impact and finish positions
feat: add phase confidence and manual correction
feat: support camera-specific phase detection
```

---

## Milestone 10: Swing Measurement Engine

### Tasks

* Create geometric analysis utilities
* Calculate joint angles
* Calculate line tilt
* Calculate normalized distances
* Measure setup posture
* Measure head movement
* Estimate rotation
* Measure tempo
* Evaluate finish balance
* Add unit tests

### Completion Criteria

* Measurements are deterministic
* Calculations use normalized body dimensions
* Invalid landmarks do not produce misleading results
* Core analysis utilities have test coverage

### Branch

```text
feature/analysis-engine
```

### Planned Commits

```text
feat: add geometric swing analysis utilities
feat: calculate setup and posture metrics
feat: measure head movement and rotation
feat: calculate swing tempo and finish balance
test: add swing measurement unit tests
```

---

## Milestone 11: Explainable Rule Engine

### Tasks

* Define finding data structure
* Create setup-related rules
* Create backswing-related rules
* Create downswing-related rules
* Create impact-related rules
* Create finish-related rules
* Add confidence thresholds
* Add camera-angle restrictions
* Add finding severity
* Add supporting evidence

### Completion Criteria

* Findings reference actual measurements
* Unsupported findings are never shown
* No more than three primary findings are prioritized
* Every finding explains why it was triggered

### Branch

```text
feature/rule-engine
```

### Planned Commits

```text
feat: define explainable swing finding model
feat: add setup and backswing analysis rules
feat: add downswing and impact analysis rules
feat: add finish and balance analysis rules
feat: prioritize findings by confidence and severity
```

---

## Milestone 12: AI Coaching Feedback

### Tasks

* Configure OpenAI SDK in backend
* Create structured coaching prompt
* Send metrics and findings
* Optionally include selected key frames
* Require structured JSON response
* Validate AI response with Zod
* Save feedback to PostgreSQL
* Handle request failures
* Add rate limiting
* Add analysis limitations

### Completion Criteria

* Feedback only references provided evidence
* AI produces no more than three priorities
* Feedback includes positive observations
* Recommended drills are practical
* Invalid responses are rejected safely
* OpenAI credentials remain server-side

### Branch

```text
feature/ai-feedback
```

### Planned Commits

```text
chore: configure OpenAI backend integration
feat: generate structured golf coaching feedback
feat: validate and persist AI analysis responses
feat: add coaching drills and practice plans
fix: handle AI feedback failures safely
```

---

## Milestone 13: Real Analysis Results

### Tasks

* Replace mock data with real metrics
* Display detected swing phases
* Display real score cards
* Display prioritized findings
* Display drills and practice plan
* Add key-frame previews
* Add limitations and confidence indicators
* Add download-free shareable presentation view if useful

### Completion Criteria

* Analysis results are fully driven by processed swing data
* Scores, findings, and drills are consistent
* The page remains clear and visually impressive
* Users understand confidence and limitations

### Branch

```text
feature/analysis-results
```

### Planned Commits

```text
feat: connect real metrics to analysis results
feat: display detected phases and key frames
feat: render prioritized coaching findings
feat: add personalized drills and practice plan
feat: display analysis confidence and limitations
```

---

## Milestone 14: Swing History and Comparison

### Tasks

* Add search and filtering
* Add pagination if necessary
* Add analysis deletion
* Select two swings
* Validate comparison compatibility
* Add synchronized playback
* Compare scores and metrics
* Generate improvement summary
* Add progress charts

### Completion Criteria

* Users can find previous swings easily
* Users can compare compatible recordings
* Changes are clearly visualized
* Users can delete their own analyses safely

### Branch

```text
feature/swing-comparison
```

### Planned Commits

```text
feat: add searchable swing analysis history
feat: add swing filters and deletion
feat: create swing comparison selection flow
feat: add synchronized comparison playback
feat: visualize performance changes over time
```

---

## Milestone 15: Reliability and Error Handling

### Tasks

* Handle no golfer detected
* Handle multiple people detected
* Handle incomplete body visibility
* Handle poor lighting
* Handle camera movement
* Handle unsupported camera angle
* Handle upload failure
* Handle processing failure
* Handle AI failure
* Add retry workflows
* Improve logging

### Completion Criteria

* Errors are understandable
* Users receive actionable recording guidance
* Failures do not create broken database states
* Processing can be retried safely

### Branch

```text
feature/reliability
```

### Planned Commits

```text
fix: improve video recording validation
fix: handle pose processing failures
fix: add retryable analysis states
fix: improve upload and AI error recovery
chore: add structured backend logging
```

---

## Milestone 16: Testing and Quality

### Tasks

* Add frontend component tests
* Add backend integration tests
* Add authentication tests
* Add ownership tests
* Add upload validation tests
* Add analysis engine tests
* Add rule engine tests
* Test mobile layouts
* Test multiple video formats
* Test multiple camera angles

### Completion Criteria

* Critical workflows are covered
* Both applications build successfully
* No major responsive issues remain
* Core calculations behave consistently

### Branch

```text
feature/testing
```

### Planned Commits

```text
test: add authentication integration coverage
test: add swing ownership and API tests
test: add upload validation coverage
test: expand analysis and rule engine coverage
test: add frontend workflow tests
```

---

## Milestone 17: Deployment

### Tasks

* Deploy frontend to Vercel
* Deploy backend to Render
* Configure Neon production database
* Configure Cloudinary production settings
* Add production environment variables
* Restrict CORS
* Add rate limits
* Run database migrations
* Verify mobile and desktop production builds
* Verify video cleanup on deletion

### Completion Criteria

* Public application is accessible
* Frontend communicates with backend
* Authentication works in production
* Video upload and analysis work in production
* Secrets are not exposed
* Production errors are handled safely

### Branch

```text
feature/deployment
```

### Planned Commits

```text
chore: configure production environment
chore: prepare frontend for Vercel deployment
chore: prepare backend for Render deployment
fix: secure production CORS and rate limits
chore: finalize production database migrations
```

---

## Milestone 18: Portfolio and Recruiter Presentation

### Tasks

* Write polished README
* Add screenshots
* Add architecture diagram
* Add feature overview
* Add local setup instructions
* Add technical challenges
* Add future improvements
* Record demo video
* Add project to portfolio
* Add project to LinkedIn
* Confirm public repository quality

### Completion Criteria

* Recruiters can understand the project quickly
* README clearly explains the technical depth
* Portfolio contains a strong project case study
* Demo video highlights the most impressive workflow
* Repository has a clean commit history

### Planned Commits

```text
docs: expand README with setup and architecture
docs: add project screenshots and feature overview
docs: document technical challenges and decisions
docs: finalize portfolio project presentation
```

---

## Definition of Done

TempoAI will be considered complete when:

* A user can register and log in
* A user can upload a golf swing video
* The application can detect body landmarks
* The application can identify major swing phases
* The application can calculate measurable swing metrics
* The application can generate explainable findings
* The application can generate structured AI coaching
* Analyses are saved to user history
* Two swings can be compared
* The application works on desktop and mobile
* The application is deployed publicly
* The repository and portfolio presentation are recruiter-ready
