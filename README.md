# Tools and Premium Access Django Project

## Overview
This Django project provides a platform to manage and access various tools with a premium access system. Users can browse tools, request premium access, and submit reviews for tools if they have premium status. Admin users can manage tools, review premium access requests, and approve or reject them.

## Key Features
- Tool Management: Create, update, delete, and list tools with rich content, images, videos, and source code links.
- Premium Access System: Users can request premium access to unlock additional features and content.
- Premium Request Workflow: Users submit requests, admins review and approve/reject requests.
- User Reviews: Premium users can submit ratings and reviews for tools.
- Admin Dashboard: Overview of premium requests, user statistics, and trends.
- Email Notifications: Automated emails for premium request events (new request, approval, rejection, cancellation).
- Access Control: Only premium users or admins can access premium content and submit reviews.

## Project Structure
- `tools/`: Django app managing tools, premium requests, reviews, and related views, forms, templates, and URLs.
- `core/`: Core app with base templates and common functionality.
- `media/`: Media files including uploaded images and videos.
- `static/`: Static assets like CSS, JS, and images.
- `myenv/`: Python virtual environment.
- `manage.py`: Django management script.
- `README.md`: Project documentation.

## Models
- `Tool`: Represents a tool with title, category, content, media URLs, author, and timestamps.
- `PremiumRequest`: Tracks user requests for premium access with status and timestamps.
- `ToolReview`: Stores user reviews and ratings for tools.

## Views and URLs
- Tool listing, detail, update, and delete views.
- Premium request submission, status, cancellation, and admin approval/rejection views.
- Admin dashboard for managing premium requests and viewing statistics.

## Templates
- Tool-related templates for listing, detail, forms, and premium request workflows.
- Base templates for consistent UI.

## Usage
1. Set up the Python virtual environment and install dependencies from `requirements.txt`.
2. Run database migrations.
3. Create a superuser for admin access.
4. Start the Django development server.
5. Access the tools app to browse tools, request premium access, and manage tools (admin).
6. Use the admin dashboard to review and manage premium requests.

## Testing
- Critical features include premium request workflow, tool access control, review submission, and admin actions.
- Recommended to perform thorough testing of all user roles and edge cases.

## Future Improvements
- Add image upload support for tools.
- Enhance review management with edit/delete options.
- Improve UI/UX with better notifications and form validations.
- Add bulk actions in admin dashboard.

## Contact
For support or inquiries, contact the project maintainer.
