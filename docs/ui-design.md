# TempoAI UI Design

## Design Goal

TempoAI should feel like a premium sports-performance platform rather than a school project.

The interface should communicate:

* Precision
* Motion
* Athletic performance
* Modern technology
* Clear coaching feedback
* Professional data visualization

The application should feel polished enough for recruiters to explore while remaining simple enough for golfers to understand immediately.

---

## Visual Direction

TempoAI will use a dark sports-tech design system with strong contrast and restrained accent colors.

### Recommended Style

* Dark navy or charcoal background
* White and soft gray text
* Lime, green, or electric blue accent color
* Large video-focused cards
* Rounded panels with subtle borders
* Clean typography
* Smooth transitions
* Minimal gradients
* Data visualization used carefully
* Strong spacing and visual hierarchy

The interface should not feel overly futuristic, cluttered, or game-like.

---

## Typography

Recommended typography:

* Headings: Inter, Manrope, or Geist
* Body text: Inter or Geist
* Metrics: Semibold or bold numerical styling

Typography should prioritize readability, especially for analysis results and coaching feedback.

---

## Core Navigation

Authenticated users will use a responsive application shell.

### Desktop Navigation

A left sidebar will include:

* Dashboard
* New Analysis
* Swing History
* Compare Swings
* Profile
* Logout

### Mobile Navigation

Mobile users will use either:

* A top navigation bar with a menu button
* A slide-out navigation drawer

The current page should always be visually clear.

---

## Page 1: Landing Page

### Purpose

Introduce TempoAI and encourage visitors to try the application.

### Main Sections

#### Navigation

* TempoAI logo
* Features
* How It Works
* Login
* Get Started button

#### Hero

The hero should include:

* Strong headline
* Short product description
* Primary call-to-action
* Secondary demo call-to-action
* Product preview showing a swing video with a pose skeleton overlay

Suggested headline:

> Smarter swing feedback from every frame.

Suggested supporting text:

> Upload your golf swing, track key body positions, and receive personalized coaching powered by computer vision and AI.

#### Feature Highlights

Three or four feature cards:

* Pose Tracking
* Swing Metrics
* AI Coaching
* Progress Tracking

#### How It Works

Three steps:

1. Upload your swing
2. Analyze movement
3. Improve with focused feedback

#### Product Preview

A large mock analysis interface showing:

* Video player
* Key swing positions
* Score cards
* Coaching priorities

#### Final Call-to-Action

Encourage the user to create an account and analyze a swing.

---

## Page 2: Login

### Content

* TempoAI branding
* Email field
* Password field
* Login button
* Link to registration
* Optional short product statement

### Design

The login page should be simple and focused, with no unnecessary distractions.

---

## Page 3: Register

### Content

* Name
* Email
* Password
* Confirm password
* Handedness selection
* Create account button
* Link to login

---

## Page 4: Dashboard

### Purpose

Give users a quick view of their swing-analysis activity and progress.

### Header

* Welcome message
* New Analysis button
* User avatar or profile control

### Summary Metrics

* Total swings analyzed
* Average swing score
* Most analyzed club
* Recent improvement
* Latest analysis date

### Recent Analyses

Display recent swings as cards with:

* Video thumbnail
* Swing title
* Club
* Camera angle
* Date
* Overall score
* Processing status
* Main finding

### Progress Section

Include one or two simple charts:

* Overall score over time
* Tempo or stability score over time

### Empty State

New users should see:

* Clear explanation
* Recording tips
* Upload first swing button

---

## Page 5: New Analysis

### Purpose

Guide the user through uploading a valid golf swing video.

### Upload Form

Fields:

* Swing title
* Club
* Camera angle
* Handedness
* Optional notes
* Video file

### Upload Area

Use a large drag-and-drop area with:

* File icon
* Accepted formats
* Maximum video length
* Maximum file size
* Browse button

### Video Preview

After selecting a video, display:

* Video preview
* File name
* Duration
* File size
* Replace button
* Remove button

### Recording Guidance

Show camera-angle-specific instructions.

#### Down-the-Line

* Position camera behind the golfer
* Align camera near hand height
* Keep the target line visible
* Keep the golfer and club fully in frame

#### Face-On

* Position camera directly across from the golfer
* Keep the full body and club visible
* Keep the camera stationary
* Avoid extreme camera angles

### Submission

Primary button:

> Analyze Swing

The button should remain disabled until validation passes.

---

## Page 6: Processing

### Purpose

Clearly communicate that the swing is being analyzed.

### Processing Steps

Display a visual progress sequence:

1. Upload complete
2. Detecting body landmarks
3. Identifying swing positions
4. Calculating swing metrics
5. Generating coaching feedback

### Design

Use:

* Animated progress indicator
* Swing silhouette or skeleton animation
* Helpful processing message
* Estimated steps rather than an exact completion time

### Failure State

Show:

* Clear reason for failure
* Recording suggestion
* Retry button
* Return to upload button

---

## Page 7: Analysis Results

### Purpose

Present the most impressive and useful part of TempoAI.

### Header

Include:

* Swing title
* Date
* Club
* Camera angle
* Overall score
* Compare button
* Delete action

### Video Analysis Area

Display:

* Video player
* Skeleton overlay
* Playback controls
* Playback speed
* Frame stepping
* Overlay toggle
* Measurement toggle
* Fullscreen option

### Swing Phase Timeline

Include labeled positions:

* Address
* Takeaway
* Top
* Downswing
* Impact
* Finish

Selecting a phase should move the video to that frame.

### Score Cards

Display:

* Setup
* Rotation
* Tempo
* Stability
* Finish

Each card should include:

* Score
* Label
* Short interpretation

### Coaching Summary

Display:

* Overall summary
* Positive observation
* Main improvement focus

### Priority Findings

Show no more than three primary findings.

Each card should include:

* Finding title
* Severity
* Confidence
* Relevant swing phase
* Supporting metric
* Explanation
* Recommended drill

### Swing Metrics

Display measurable values such as:

* Spine angle
* Shoulder tilt
* Hip tilt
* Head movement
* Tempo ratio
* Lead-arm bend
* Finish balance

Metrics should be presented clearly without overwhelming the user.

### Practice Plan

Provide a short session plan containing:

* Warm-up
* Primary drill
* Reinforcement drill
* Number of repetitions
* Suggested recording checkpoint

### Limitations

Include a visible note explaining that results depend on:

* Camera placement
* Lighting
* Video quality
* Pose-detection confidence
* A single recorded swing

---

## Page 8: Swing History

### Purpose

Allow users to review previous analyses.

### Filters

* Club
* Camera angle
* Date
* Score range
* Processing status

### Search

Allow users to search by swing title or club.

### Analysis Cards

Each card should show:

* Thumbnail
* Title
* Club
* Camera angle
* Date
* Overall score
* Main finding
* View button

### Empty State

Show a call-to-action to upload the first swing.

---

## Page 9: Compare Swings

### Purpose

Help users identify changes between two analyses.

### Selection

Allow the user to select two completed swings.

Prefer matching:

* Camera angle
* Club
* Handedness

Display a warning if the selected swings are difficult to compare.

### Comparison Layout

Include:

* Side-by-side videos
* Synced playback
* Matching phase controls
* Score comparison
* Metric comparison
* Improvement indicators
* AI-generated comparison summary

### Key Comparison Metrics

* Overall score
* Tempo
* Head movement
* Spine angle
* Rotation
* Stability
* Finish balance

---

## Page 10: Profile

### Content

* Name
* Email
* Handedness
* Preferred club
* Profile image or initials
* Account creation date

### Settings

* Update profile
* Change password
* Default handedness
* Default camera angle
* Delete account

---

## Shared Components

TempoAI should include reusable components for:

* Button
* Input
* Select
* Textarea
* Card
* Badge
* Modal
* Tooltip
* Empty state
* Loading skeleton
* Progress indicator
* Metric card
* Score ring
* Video player
* Swing phase selector
* Finding card
* Drill card
* Analysis card
* Chart container
* Confirmation dialog

---

## Responsive Design

### Desktop

* Persistent sidebar
* Wide analysis layout
* Video and feedback shown side-by-side where possible
* Multi-column metric cards

### Tablet

* Collapsible navigation
* Two-column layouts when space allows
* Stacked video and coaching sections

### Mobile

* Single-column layout
* Touch-friendly controls
* Horizontal scrolling only where necessary
* Condensed metric cards
* Sticky primary actions
* Simplified chart labels

The video player and analysis controls must remain usable on smaller screens.

---

## Motion and Interaction

Use Framer Motion for restrained animation.

Recommended motion:

* Page transitions
* Card entrance animations
* Upload progress
* Processing-state animation
* Score count-up
* Timeline selection
* Modal transitions
* Hover effects

Avoid excessive movement that distracts from the swing analysis.

---

## Accessibility

TempoAI should include:

* Keyboard-accessible controls
* Visible focus states
* Descriptive button labels
* Proper form labels
* Sufficient contrast
* Captions or text alternatives where possible
* Error messages connected to inputs
* Controls that do not rely on color alone

---

## Initial Mock Data

Before backend integration, the frontend will use mock data for:

* Dashboard metrics
* Recent analyses
* Swing scores
* Coaching findings
* Swing metrics
* Progress charts
* Swing history
* Swing comparisons

This will allow the visual experience to be completed before implementing authentication, uploads, and analysis processing.
