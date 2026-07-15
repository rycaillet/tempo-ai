# TempoAI System Architecture

## Overview

TempoAI is a full-stack golf swing analysis application that combines video processing, computer vision, structured swing measurements, and generative AI coaching.

The application uses a React frontend, an Express API, PostgreSQL for persistent data, Cloudinary for video storage, MediaPipe for pose detection, and the OpenAI API for personalized coaching feedback.

---

## High-Level Architecture

```text
User
  |
  v
React Frontend
  |
  | REST API
  v
Express Backend
  |
  +--------------------+
  |                    |
  v                    v
PostgreSQL          OpenAI API
via Prisma          Coaching Feedback
  |
  v
User and Swing Data

React Frontend
  |
  +--------------------+
  |                    |
  v                    v
Cloudinary         MediaPipe
Video Storage      Pose Detection