# Project Guidelines for AI Agents

## Overview

This is a Hugo-based technical blog (blog.stderr.at) using the custom YAUB theme. Content is primarily written in AsciiDoc (.adoc) format, focusing on OpenShift, Kubernetes, GitOps, and DevOps topics.

## Project Structure

```
Blog-Source/
├── content/           # Blog posts organized by category
│   ├── GitOpsCollection/    # GitOps series articles
│   ├── OpenShift-Platform/  # OpenShift articles
│   ├── SecureSupplyChain/   # Supply chain security series
│   ├── ansible/             # Ansible articles
│   └── ...
├── themes/yaub/       # Custom Hugo theme
│   ├── layouts/       # Hugo templates
│   └── static/css/    # Stylesheets (modular CSS)
└── static/            # Static assets
```

## Content Standards

### AsciiDoc Blog Posts

- **Naming**: `YYYY-MM-DD-Title-With-Dashes.adoc`
- **Frontmatter**: YAML format with title, description, date, authors, categories, tags
- **Images**: Store in `content/<category>/images/`, reference with `:imagesdir:`

### Required Frontmatter Fields

```yaml
title: "[Series] Descriptive Title"
description: "SEO summary"
date: "YYYY-MM-DD"
authors: [Thomas Jungbauer]
type: post
draft: false
categories: [Category1, Category2]
tags: ["tag1", "tag2"]
```

### Optional Featured Image

```yaml
featured_image: /category/images/Logo-Name.png
show_featured_image_summary: true    # Display in post listings
show_featured_image_article: true    # Display at top of article
featured_image_position: 50% 35%     # CSS background-position (optional)
```

### AsciiDoc Conventions

- Use `<!--more-->` for excerpt separator
- Headings start at `==` (H2) - title is H1 from frontmatter
- Code blocks: `[source,language]` with `----` delimiters
- Callouts: `<1>`, `<2>` in code, explained below block
- Admonitions: NOTE, TIP, WARNING, IMPORTANT, CAUTION
- External links: `https://url[text^]` (^ for new tab)

## Theme Development

### CSS Structure

Modular CSS in `themes/yaub/static/css/modular/`:
- `components/` - UI components (sidebar, pagefind, etc.)
- Follow existing patterns for consistency

### Hugo Templates

Located in `themes/yaub/layouts/`:
- Use Hugo templating syntax
- Partials in `layouts/partials/`

## Technical Context

- **Primary Topics**: OpenShift, Kubernetes, Argo CD, GitOps, Helm Charts, Red Hat technologies
- **Author Style**: Technical tutorials with step-by-step instructions, code examples with callout explanations
- **Helm Charts**: Author maintains charts at https://github.com/tjungbauer/helm-charts

## Do NOT

- Create posts without proper frontmatter
- Use H1 (`=`) headings in content body
- Forget the `<!--more-->` excerpt separator
- Store images outside the category's images folder
