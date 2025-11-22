f# Flutter SDK Manager - Implementation Plan

## Overview
Add comprehensive Flutter SDK management: discover versions from official sources, download, install, and manage multiple SDK versions with environment PATH management.

## Features to Implement

### 1. SDK Version Discovery
- Fetch available Flutter versions from GitHub API
- Show stable, beta, and dev channels
- Display release dates and changelog links
- Cache version list locally

### 2. SDK Download & Installation
- Download Flutter SDK ZIP from official source
- Extract to managed SDK directory
- Verify installation
- Show download progress
- Support resume on failure

### 3. SDK Version Management
- List all installed SDKs
- Install new SDK versions
- Remove SDK versions
- Switch between SDK versions
- Set default SDK

### 4. Environment PATH Management
- Automatically add Flutter to PATH
- Remove Flutter from PATH
- Update PATH when switching SDKs
- Windows: Registry-based PATH management
- Linux/macOS: Shell config file management

### 5. Per-Project SDK Override
- Allow projects to use specific SDK versions
- Store project-specific SDK in settings
- Auto-switch SDK when opening project

## Technical Implementation

### New Services
- `services/sdk_manager_service.py` - SDK download, install, management
- `utils/path_manager.py` - Cross-platform PATH management
- `utils/downloader.py` - File download with progress

### New UI Components
- `ui/sdk_manager_dialog.py` - Main SDK management interface
- `ui/sdk_download_dialog.py` - Download progress dialog
- `ui/path_manager_dialog.py` - PATH management UI

### API Integration
- GitHub Releases API: `https://api.github.com/repos/flutter/flutter/releases`
- Flutter Storage: `https://storage.googleapis.com/flutter_infra_release/releases/`

## Implementation Steps
1. Create SDK manager service with version discovery
2. Implement download functionality
3. Add SDK installation (extract and verify)
4. Create PATH management utilities
5. Build SDK manager UI
6. Integrate with existing settings

