# Changelog

All notable changes to the TickTick MCP Server will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [2.0.0] - 2024-12-11

### Added

#### New Services
- **Smart Service**: AI-powered task scheduling and smart views
  - `ticktick_get_today` - Today's tasks sorted by priority
  - `ticktick_get_tomorrow` - Tomorrow's tasks
  - `ticktick_get_overdue` - Overdue tasks
  - `ticktick_get_next_7_days` - Weekly task view
  - `ticktick_search_tasks` - Full-text search
  - `ticktick_get_unscheduled` - Tasks without dates
  - `ticktick_get_high_priority` - High priority filter
  - `ticktick_schedule_day` - AI scheduling suggestions
  - `ticktick_productivity_summary` - Productivity insights

- **Cache System**: Local task cache for faster operations
  - `ticktick_cache_register` - Register task in cache
  - `ticktick_cache_search` - Fast local search
  - `ticktick_cache_refresh` - Sync from API
  - `ticktick_cache_stats` - Cache statistics
  - CSV import/export support

- **Calendar Integration**: Calendar event management
  - `ticktick_calendar_today` - Today's events
  - `ticktick_calendar_week` - This week's events
  - `ticktick_calendar_events` - Custom date range
  - `ticktick_calendars_list` - List connected calendars

- **User/Settings Tools**
  - `ticktick_get_profile` - User profile information
  - `ticktick_get_inbox_id` - Get inbox project ID
  - `ticktick_get_timezone` - User timezone
  - `ticktick_get_settings` / `ticktick_update_settings`

#### Infrastructure
- Docker support with multi-stage build
- GitHub Actions CI/CD workflows
- Issue templates (bug report, feature request)
- Helper scripts (`get_token.py`, `test_connection.py`)
- Example files for common workflows

### Changed
- Expanded tool count from 56 to 80+
- Enhanced server instructions with quick start guide
- Improved error handling and formatting

### Fixed
- Token refresh handling
- Date parsing for various formats

## [1.0.0] - 2024-12-01

### Added
- Initial release
- OAuth2 authentication (v1 API)
- Username/password authentication (v2 API)
- Task management (CRUD, batch operations)
- Project management
- Tag management
- Habit tracking
- Focus/Pomodoro timer
- Statistics and analytics

---

## Version History

| Version | Date | Highlights |
|---------|------|------------|
| 2.0.0 | 2024-12-11 | Smart tools, cache system, calendar |
| 1.0.0 | 2024-12-01 | Initial release |

[Unreleased]: https://github.com/MostafaSuliman/TickTick-MCP/compare/v2.0.0...HEAD
[2.0.0]: https://github.com/MostafaSuliman/TickTick-MCP/compare/v1.0.0...v2.0.0
[1.0.0]: https://github.com/MostafaSuliman/TickTick-MCP/releases/tag/v1.0.0
