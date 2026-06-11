# ISI V4 Design System

This document outlines the core design language for the ISI V4 Terminal Redesign.

## 1. Theme & Colors
**Concept**: Dark Terminal (Modern Trading Terminal / Bloomberg Terminal Modernized)

- **Primary Background**: `#05070B` (Deep terminal black)
- **Secondary Background**: `#0B1220` (Sidebar and Right Panel background)
- **Card Background**: `#111827` (Card elements)
- **Borders**: `#1F2937` (Subtle dividers)

### Text Colors
- **Text Primary**: `#FFFFFF` (High emphasis)
- **Text Secondary**: `#9CA3AF` (Muted/labels)

### Status Colors
- **RISK ON / Accumulate / Healthy**: `#00E676`
- **NETRAL / Hold / Weakening**: `#FFD54F`
- **RISK OFF / Reduce / Exit**: `#FF5252`

## 2. Typography
- **Font Family**: `Inter`, sans-serif (Clean, modern, highly legible at small sizes)
- **Font Sizes**:
  - Hero Status: `2.5rem` / `40px` (Bold)
  - Card Value / Key Metric: `1.5rem` / `24px` (Bold)
  - Primary Content: `1rem` / `16px` (Regular/Medium)
  - Secondary Content / Subtitle: `0.875rem` / `14px` (Regular)
  - Labels / Micro-copy: `0.75rem` / `12px` (Medium/SemiBold)

## 3. Cards
- **Background**: `#111827`
- **Border**: 1px solid `#1F2937`
- **Border Radius**: `0.75rem` (12px)
- **Padding**: `1.25rem` (20px) internally.
- *Cards must never have heavy box-shadows, maintaining a flat terminal feel.*

## 4. Badges & Status Pills
- **Border Radius**: `2rem` (Pill shape)
- **Padding**: `4px 12px` for normal pills, `8px 24px` for Hero Action.
- **Styling**: 10% opacity background of the core status color, with a 30% opacity border of the same color. Text is 100% opacity status color.

## 5. Progress Bars
- **Height**: `4px`
- **Track**: `#1F2937`
- **Fill**: Variable based on score (e.g., `#00E676` for >60, `#FFD54F` for 40-60, `#FF5252` for <40).
- **Border Radius**: `2px`

## 6. Spacing & Grid
- **Global Gap**: `1rem` (16px) between cards.
- **Desktop Grid**: 12-column CSS Grid.
  - Sidebar: Fixed `260px`
  - Right Panel: Fixed `320px`
  - Center Content: `1fr` (Flexible space)
- **Mobile Grid**: 1-column stack. No horizontal scrolling ever.

## 7. Table vs Card Policy
- **Desktop**: Allows toggling between 'Card View' and 'Table View' for Leaders, Turnaround, and Exit tabs. Table headers remain fixed/sticky.
- **Mobile**: Strict **Cards Only** policy. Tables are completely removed from the DOM or hidden via CSS, replaced by vertical card stacks. No information loss.
