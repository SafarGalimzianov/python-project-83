### Hexlet tests and linter status:
[![Actions Status](https://github.com/SafarGalimzianov/python-project-83/actions/workflows/hexlet-check.yml/badge.svg)](https://github.com/SafarGalimzianov/python-project-83/actions)

### Test Coverage and Maintainability:
[![Test Coverage](https://api.codeclimate.com/v1/badges/68ad623e40583819f050/test_coverage)](https://codeclimate.com/github/SafarGalimzianov/python-project-83/test_coverage)
[![Maintainability](https://api.codeclimate.com/v1/badges/68ad623e40583819f050/maintainability)](https://codeclimate.com/github/SafarGalimzianov/python-project-83/maintainability)

### Render link:
https://python-project-83-og9i.onrender.com
___

### Problem

Web developers and SEO specialists need to quickly analyze web pages for basic SEO metrics like title tags, meta descriptions, and H1 headers. Manual checking of multiple URLs is time-consuming and error-prone.
In order to help developers and marketers optimize their websites, I decided to create a page analyzer web-service to automatically check and track SEO elements of web pages.
___

### Requirements

#### Availability
- Everyone on the Internet should be able to visit the service at any time
- All users should have the same access to analyze URLs and view results

#### Functionality
- Everyone on the Internet should be able to add URLs for analysis and view existing URL checks
- Users should be able to run SEO checks on URLs to extract title, H1, meta description, and HTTP status
- The service should store check history and display paginated results

#### Design
- The service HTML templates should not include inline scripts and CSS, but only HTML5 and Bootstrap5
- The language of the service should be Russian (as per current implementation)
- The service design should follow modern clean corporate style with proper responsive layout

#### Other
- The service should be deployed on PaaS (Render)
- The service should load each page efficiently with proper database indexing
- The service's interface should be user-friendly with clear navigation and flash messages
- The project is based on Python (3.10+), Flask (3.0+), PostgreSQL (connection pooling) and requests for web scraping
___

### Architecture

#### Structure
This is a project that solves a specific SEO analysis problem without high load requirements.
The structure follows Flask best practices with clear separation of concerns.
The Flask project includes organized static CSS files and uses a modular approach with separate modules for database operations, business logic, and web scraping.
Views are handled by route functions in [`page_analyzer.app`](page_analyzer/app.py) with proper error handling and flash messaging.

#### Data
The project's communication with database is handled by [`AppRepository`](page_analyzer/app_repository.py) (SQL queries) and [`ConnectionPool`](page_analyzer/db_pool.py) (connection pool) classes.
DB contains tables URLS (stored URLs with creation dates) and URL_CHECKS (check results with SEO data).
Smart indexing strategy with PostgreSQL triggers for auto-incrementing check IDs per URL.

#### Security
The security is handled by input sanitization in [`sanitize_url_input`](page_analyzer/service.py), CSP headers, and parameterized SQL queries.
The connection to DB is secured by storing credentials in environment variables.
HTML output is automatically escaped by Jinja2 templates.

#### Errors
HTTP errors (400, 404, 422, 500) are handled gracefully with custom error pages.
Request errors during URL checking are caught and displayed to users via flash messages.
Database connection errors are properly handled with connection pooling.

#### Performance and stability
Performance is optimized through database indexing, connection pooling, and efficient pagination.
Stability is ensured by comprehensive error handling, request timeouts, and proper resource management.
___

### Release
Current implementation features

#### Structure
Modular Flask application with clear separation:
- [`page_analyzer.app`](page_analyzer/app.py): Main Flask routes and error handling
- [`page_analyzer.service`](page_analyzer/service.py): Business logic and web scraping
- [`page_analyzer.app_repository`](page_analyzer/app_repository.py): Database operations
- [`page_analyzer.db_pool`](page_analyzer/db_pool.py): Connection pool management

#### Data
2 main tables with optimized relationships:
- urls: Stores unique URLs with creation timestamps
- url_checks: Stores check results with auto-incrementing check_id per URL
Optimizations: Indexed columns, PostgreSQL triggers, and efficient pagination queries

#### Security
Input sanitization, CSP headers, parameterized queries, and environment-based configuration.

#### Errors
Comprehensive error handling with custom templates and user-friendly flash messages.

#### Performance and stability
Connection pooling, database indexing, request timeouts, and proper resource cleanup.
