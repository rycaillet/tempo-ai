# TempoAI

TempoAI is an AI-powered golf swing analysis platform that combines computer vision, motion analysis, and generative AI to provide golfers with clear, personalized swing feedback.

Users will be able to upload a golf swing video, view pose tracking and key swing positions, review measurable swing metrics, and receive prioritized coaching recommendations with practice drills.

## Project Purpose

TempoAI is being developed as a professional software engineering portfolio project.

The application is designed to demonstrate:

* Full-stack application development
* Responsive user interface design
* Video upload and playback
* Computer vision with MediaPipe
* Motion and posture analysis
* Explainable rule-based feedback
* Generative AI integration
* Secure authentication
* PostgreSQL data modeling
* Cloud deployment

TempoAI will not include payments, subscriptions, or billing features.

## Planned Features

* User registration and login
* Golf swing video uploads
* Face-on and down-the-line recording support
* Pose landmark detection
* Skeleton overlay
* Key swing phase detection
* Frame-by-frame video controls
* Swing posture and movement metrics
* Explainable swing findings
* AI-generated coaching feedback
* Personalized practice drills
* Swing analysis history
* Side-by-side swing comparisons
* Progress tracking
* Responsive desktop and mobile design

## Technology Stack

### Frontend

* React
* TypeScript
* Vite
* Tailwind CSS
* React Router
* Framer Motion
* Lucide React
* Recharts

### Backend

* Node.js
* Express
* TypeScript
* Prisma ORM
* PostgreSQL
* JSON Web Tokens
* bcrypt
* Zod

### Computer Vision and AI

* MediaPipe Pose Landmarker
* OpenAI API

### Infrastructure

* Neon PostgreSQL
* Cloudinary
* Render
* Vercel

## Project Documentation

Detailed planning documents are available in the [`docs`](./docs) directory:

* [Product Requirements](./docs/product-requirements.md)
* [System Architecture](./docs/architecture.md)
* [UI Design](./docs/ui-design.md)
* [Development Roadmap](./docs/roadmap.md)

## Planned Application Flow

1. A user creates an account or logs in.
2. The user uploads a golf swing video.
3. TempoAI validates and processes the recording.
4. MediaPipe detects body landmarks throughout the swing.
5. The analysis engine identifies key swing phases and calculates metrics.
6. A rule-based system produces explainable findings.
7. OpenAI converts the findings into personalized coaching feedback.
8. The completed analysis is saved to the user's history.
9. The user can compare the swing with previous recordings.

## Current Status

**Milestone 1: Product Planning**

Completed:

* Product requirements
* System architecture
* UI and user experience planning
* Development roadmap
* Initial repository structure

Next:

* Initialize the React and TypeScript frontend
* Initialize the Express and TypeScript backend
* Configure the development environment
* Add the first backend health endpoint

## Disclaimer

TempoAI is intended as an educational and practice-support tool. Its feedback will depend on video quality, camera placement, pose-detection confidence, and the limitations of analyzing a single recorded swing.

It is not intended to replace professional golf instruction.
