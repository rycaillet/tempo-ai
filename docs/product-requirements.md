# TempoAI Product Requirements

## Overview

TempoAI is an AI-powered golf swing analysis platform that helps golfers improve their swing by combining computer vision, motion analysis, and generative AI. Users can upload a golf swing video, receive visual analysis with pose tracking, identify key swing positions, and get personalized coaching feedback with recommended practice drills.

The goal of TempoAI is not to replace a golf instructor, but to provide accessible, data-driven swing feedback that golfers can use between lessons or practice sessions.

---

## Problem Statement

Golf improvement is difficult without immediate feedback.

Most amateur golfers rely on recording swing videos with their phones, but interpreting those videos requires experience or access to an instructor. Existing launch monitors and professional coaching platforms can be expensive, while many recreational golfers simply want practical feedback after a practice session.

TempoAI bridges this gap by automatically analyzing a recorded swing and presenting clear, understandable insights supported by measurable data.

---

## Target Audience

Primary users:

- Amateur golfers
- Recreational golfers
- Golf students
- Players practicing at driving ranges
- Golfers who record their own swings

Secondary audience:

- Golf instructors
- Friends reviewing swings together

---

## Goals

Users should be able to:

- Create an account
- Upload a golf swing video
- Choose the camera angle
- View an analyzed swing with body landmarks
- Identify important swing positions
- Receive AI-generated coaching feedback
- Review recommended practice drills
- Track previous swing analyses over time

---

## Core Features

### Authentication

- Register
- Login
- Secure JWT authentication

### Video Upload

- Upload golf swing videos
- Support multiple video formats
- Preview before submission

### Computer Vision

- Detect golfer body landmarks
- Display skeleton overlay
- Identify key swing positions

### Swing Analysis

- Calculate body angles
- Measure posture
- Estimate rotation
- Track balance
- Evaluate swing tempo

### AI Coaching

- Personalized feedback
- Prioritized improvement areas
- Practice drill recommendations
- Session summary

### History

- View previous analyses
- Compare swing improvements
- Review historical feedback

---

## User Flow

1. Register or login
2. Upload swing video
3. Select camera angle
4. Video processing begins
5. Pose detection analyzes the swing
6. Swing metrics are calculated
7. AI generates coaching feedback
8. Results are displayed
9. Analysis is saved for future comparison

---

## MVP Scope

Version 1 will include:

- User authentication
- Video upload
- Pose detection
- Swing analysis
- AI coaching feedback
- Analysis history
- Responsive UI

Version 1 will NOT include:

- Live camera analysis
- Clubhead tracking
- Ball flight prediction
- Shot tracer
- Mobile application
- Social features
- Payments or subscriptions

---

## Technical Stack

Frontend

- React
- TypeScript
- Vite
- Tailwind CSS
- React Router
- Framer Motion

Backend

- Node.js
- Express
- TypeScript
- Prisma ORM
- PostgreSQL
- JWT Authentication

AI

- MediaPipe Pose
- OpenAI API

Infrastructure

- Neon PostgreSQL
- Cloudinary
- Render
- Vercel

---

## Success Criteria

TempoAI will be considered successful when a user can:

- Upload a golf swing
- Automatically receive pose detection
- View key swing positions
- Receive meaningful AI coaching
- Save analyses for future comparison
- Use the application seamlessly on desktop and mobile

The application should demonstrate modern software engineering practices, responsive UI design, computer vision, AI integration, secure authentication, and full-stack architecture suitable for a professional software engineering portfolio.