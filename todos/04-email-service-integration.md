# Email Service Integration

**Priority: HIGH** | **Effort: Medium** | **Phase: 1**
**Addresses GitHub Issue #51: Add HTML email template examples**

## Overview

Implement comprehensive email service with HTML templates, events integration, and support for multiple email providers. This enables email verification, password reset, team invitations, and other transactional emails.

## Backend Tasks

### 1. Email Service Foundation

- [ ] **Create core EmailService**

  ```python
  # File: src/py/app/services/_email.py
  from email.mime.text import MIMEText
  from email.mime.multipart import MIMEMultipart
  from email.mime.base import MIMEBase
  from email import encoders
  
  class EmailService:
      def __init__(self, settings: EmailSettings):
          self.settings = settings
          self.smtp_client = self._create_smtp_client()
      
      async def send_email(
          self,
          to_email: str,
          subject: str,
          html_content: str,
          text_content: str | None = None,
          from_email: str | None = None,
          from_name: str | None = None,
          attachments: list[EmailAttachment] | None = None
      ) -> bool:
          """Send email with HTML and optional text content"""
          
      async def send_template_email(
          self,
          template_name: str,
          to_email: str,
          context: dict,
          subject: str | None = None,
          from_email: str | None = None,
          from_name: str | None = None
      ) -> bool:
          """Send email using Jinja2 template"""
          
      async def send_bulk_email(
          self,
          recipients: list[str],
          subject: str,
          template_name: str,
          context: dict
      ) -> dict[str, bool]:
          """Send bulk emails with template"""
  ```

### 2. Email Configuration

- [ ] **Add email settings**

  ```python
  # File: src/py/app/lib/settings.py
  @dataclass
  class EmailSettings:
      # SMTP Configuration
      SMTP_HOST: str = "localhost"
      SMTP_PORT: int = 587
      SMTP_USERNAME: str = ""
      SMTP_PASSWORD: str = ""
      SMTP_USE_TLS: bool = True
      SMTP_USE_SSL: bool = False
      
      # Email Defaults
      DEFAULT_FROM_EMAIL: str = "noreply@localhost"
      DEFAULT_FROM_NAME: str = "Application"
      
      # Provider Settings (for future use)
      EMAIL_PROVIDER: str = "smtp"  # smtp, sendgrid, ses, etc.
      SENDGRID_API_KEY: str = ""
      AWS_SES_REGION: str = ""
      
      # Email Features
      EMAIL_ENABLED: bool = True
      EMAIL_DEBUG: bool = False  # Log emails instead of sending
      EMAIL_RATE_LIMIT: int = 100  # per hour
      
  # Add to main Settings
  email: EmailSettings = field(default_factory=EmailSettings)
  ```

### 3. Email Templates System

- [ ] **Create template renderer**

  ```python
  # File: src/py/app/lib/email_templates.py
  from jinja2 import Environment, FileSystemLoader, select_autoescape
  
  class EmailTemplateRenderer:
      def __init__(self, template_dir: Path):
          self.env = Environment(
              loader=FileSystemLoader(template_dir),
              autoescape=select_autoescape(['html', 'xml'])
          )
          # Add custom filters
          self.env.filters['datetime'] = self._format_datetime
          self.env.filters['currency'] = self._format_currency
      
      def render_template(
          self, 
          template_name: str, 
          context: dict
      ) -> tuple[str, str]:
          """Render HTML and text versions of template"""
          
      def _format_datetime(self, dt: datetime) -> str:
          """Custom datetime filter"""
          
      def _format_currency(self, amount: float) -> str:
          """Custom currency filter"""
  ```

### 4. Email Templates (HTML + Text)

#### Base Email Template

- [ ] **Create base email template**

  ```html
  <!-- File: src/py/app/server/templates/emails/base.html -->
  <!DOCTYPE html>
  <html lang="en">
  <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>{{ subject }}</title>
      <style>
          /* Reset styles */
          body, table, td, p, a, li, blockquote {
              -webkit-text-size-adjust: 100%;
              -ms-text-size-adjust: 100%;
          }
          
          /* Email styles */
          .email-container {
              max-width: 600px;
              margin: 0 auto;
              font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
              line-height: 1.6;
              color: #374151;
          }
          
          .header {
              background-color: #f8fafc;
              padding: 40px 20px;
              text-align: center;
              border-bottom: 1px solid #e5e7eb;
          }
          
          .content {
              padding: 40px 20px;
              background-color: #ffffff;
          }
          
          .footer {
              background-color: #f8fafc;
              padding: 20px;
              text-align: center;
              border-top: 1px solid #e5e7eb;
              font-size: 14px;
              color: #6b7280;
          }
          
          .button {
              display: inline-block;
              padding: 12px 24px;
              background-color: #2563eb;
              color: #ffffff !important;
              text-decoration: none;
              border-radius: 6px;
              margin: 20px 0;
          }
          
          .button:hover {
              background-color: #1d4ed8;
          }
          
          @media only screen and (max-width: 600px) {
              .email-container {
                  width: 100% !important;
              }
              .content {
                  padding: 20px !important;
              }
          }
      </style>
  </head>
  <body>
      <div class="email-container">
          <div class="header">
              <img src="{{ app_logo_url }}" alt="{{ app_name }}" style="max-width: 150px;">
              <h1 style="margin: 20px 0 0 0; color: #1f2937;">
                  {% block header_title %}{{ app_name }}{% endblock %}
              </h1>
          </div>
          
          <div class="content">
              {% block content %}{% endblock %}
          </div>
          
          <div class="footer">
              {% block footer %}
              <p>
                  This email was sent by {{ app_name }}<br>
                  <a href="{{ app_url }}/unsubscribe?token={{ unsubscribe_token }}">Unsubscribe</a> |
                  <a href="{{ app_url }}/contact">Contact Support</a>
              </p>
              {% endblock %}
          </div>
      </div>
  </body>
  </html>
  ```

#### Welcome Email Template

- [ ] **Create welcome email template**

  ```html
  <!-- File: src/py/app/server/templates/emails/welcome.html -->
  {% extends "emails/base.html" %}
  
  {% block header_title %}Welcome to {{ app_name }}!{% endblock %}
  
  {% block content %}
  <h2 style="color: #1f2937; margin-top: 0;">Welcome, {{ user.name or user.email }}!</h2>
  
  <p>Thank you for joining {{ app_name }}. We're excited to have you on board!</p>
  
  {% if email_verification_required %}
  <div style="background-color: #fef3c7; border: 1px solid #fbbf24; border-radius: 6px; padding: 20px; margin: 20px 0;">
      <h3 style="color: #92400e; margin-top: 0;">Please verify your email address</h3>
      <p style="color: #92400e; margin-bottom: 20px;">
          To get started, please verify your email address by clicking the button below:
      </p>
      <a href="{{ verification_url }}" class="button">Verify Email Address</a>
      <p style="font-size: 14px; color: #92400e;">
          This link will expire in 24 hours.
      </p>
  </div>
  {% endif %}
  
  <h3>Getting Started</h3>
  <ul>
      <li><a href="{{ app_url }}/profile">Complete your profile</a></li>
      <li><a href="{{ app_url }}/teams">Create or join a team</a></li>
      <li><a href="{{ app_url }}/help">Explore our help center</a></li>
  </ul>
  
  <p>If you have any questions, feel free to <a href="{{ app_url }}/contact">contact our support team</a>.</p>
  
  <p>Best regards,<br>The {{ app_name }} Team</p>
  {% endblock %}
  ```

#### Team Invitation Template

- [ ] **Create team invitation template**

  ```html
  <!-- File: src/py/app/server/templates/emails/team-invitation.html -->
  {% extends "emails/base.html" %}
  
  {% block header_title %}You're invited to join {{ team.name }}{% endblock %}
  
  {% block content %}
  <h2 style="color: #1f2937; margin-top: 0;">
      You're invited to join "{{ team.name }}"
  </h2>
  
  <p>
      <strong>{{ inviter.name or inviter.email }}</strong> has invited you to join their team 
      <strong>{{ team.name }}</strong> on {{ app_name }}.
  </p>
  
  {% if team.description %}
  <div style="background-color: #f8fafc; border-left: 4px solid #2563eb; padding: 20px; margin: 20px 0;">
      <h4 style="margin-top: 0; color: #1f2937;">About this team:</h4>
      <p style="margin-bottom: 0;">{{ team.description }}</p>
  </div>
  {% endif %}
  
  <div style="text-align: center; margin: 30px 0;">
      <a href="{{ invitation_url }}" class="button">
          Accept Invitation
      </a>
  </div>
  
  <p style="font-size: 14px; color: #6b7280;">
      This invitation will expire in {{ expires_in_days }} days. If you don't want to join this team, 
      you can safely ignore this email.
  </p>
  
  <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 30px 0;">
  
  <h3>What is {{ app_name }}?</h3>
  <p>
      {{ app_name }} is a collaborative platform that helps teams work together more effectively.
      <a href="{{ app_url }}/about">Learn more about {{ app_name }}</a>.
  </p>
  {% endblock %}
  ```

### 5. Email Event Integration

- [ ] **Create email event handlers**

  ```python
  # File: src/py/app/server/events/email.py
  from litestar.events import SimpleEventEmitter
  
  async def send_welcome_email_handler(
      user_id: UUID,
      email_service: EmailService,
      user_service: UserService
  ) -> None:
      """Send welcome email when user is created"""
      user = await user_service.get(user_id)
      await email_service.send_template_email(
          template_name="welcome",
          to_email=user.email,
          context={
              "user": user,
              "email_verification_required": not user.email_verified_at,
              "verification_url": "...",  # Generate verification URL
          }
      )
  
  async def send_team_invitation_email_handler(
      invitation_id: UUID,
      email_service: EmailService,
      team_invitation_service: TeamInvitationService
  ) -> None:
      """Send email when team invitation is created"""
      # Implementation...
  ```

- [ ] **Update event registration**

  ```python
  # Update: src/py/app/server/core.py
  app_config.listeners.extend([
      events.email.send_welcome_email_handler,
      events.email.send_team_invitation_email_handler,
      # ... existing listeners
  ])
  ```

### 6. Background Job Integration

- [ ] **Create email queue jobs**

  ```python
  # File: src/py/app/server/jobs/email.py
  from saq import Job
  
  async def send_email_job(ctx: dict, email_data: dict) -> None:
      """Background job for sending emails"""
      email_service = ctx["email_service"]
      await email_service.send_email(**email_data)
  
  async def send_template_email_job(ctx: dict, template_data: dict) -> None:
      """Background job for sending template emails"""
      email_service = ctx["email_service"]
      await email_service.send_template_email(**template_data)
  
  async def send_bulk_emails_job(ctx: dict, bulk_data: dict) -> None:
      """Background job for sending bulk emails"""
      email_service = ctx["email_service"]
      await email_service.send_bulk_email(**bulk_data)
  ```

### 7. Email Provider Integrations

- [ ] **Add SendGrid provider**

  ```python
  # File: src/py/app/lib/email_providers/sendgrid.py
  import sendgrid
  from sendgrid.helpers.mail import Mail, Email, To, Content
  
  class SendGridEmailProvider:
      def __init__(self, api_key: str):
          self.client = sendgrid.SendGridAPIClient(api_key=api_key)
      
      async def send_email(
          self,
          to_email: str,
          subject: str,
          html_content: str,
          from_email: str,
          from_name: str | None = None
      ) -> bool:
          """Send email via SendGrid"""
  ```

- [ ] **Add AWS SES provider**

  ```python
  # File: src/py/app/lib/email_providers/ses.py
  import boto3
  from botocore.exceptions import ClientError
  
  class SESEmailProvider:
      def __init__(self, region: str, access_key: str, secret_key: str):
          self.client = boto3.client(
              'ses',
              region_name=region,
              aws_access_key_id=access_key,
              aws_secret_access_key=secret_key
          )
      
      async def send_email(
          self,
          to_email: str,
          subject: str,
          html_content: str,
          from_email: str,
          from_name: str | None = None
      ) -> bool:
          """Send email via AWS SES"""
  ```

### 8. Email Analytics and Tracking

- [ ] **Create email tracking model**

  ```python
  # File: src/py/app/db/models/email_log.py
  class EmailLog(UUIDAuditBase):
      __tablename__ = "email_logs"
      
      to_email: Mapped[str] = mapped_column(String(255), index=True)
      from_email: Mapped[str] = mapped_column(String(255))
      subject: Mapped[str] = mapped_column(String(255))
      template_name: Mapped[str | None] = mapped_column(String(100))
      status: Mapped[str] = mapped_column(String(50))  # sent, failed, bounced, delivered
      provider: Mapped[str] = mapped_column(String(50))
      external_id: Mapped[str | None] = mapped_column(String(255))  # Provider message ID
      error_message: Mapped[str | None] = mapped_column(Text)
      sent_at: Mapped[datetime | None] = mapped_column(DateTime)
      delivered_at: Mapped[datetime | None] = mapped_column(DateTime)
      opened_at: Mapped[datetime | None] = mapped_column(DateTime)
      clicked_at: Mapped[datetime | None] = mapped_column(DateTime)
      
      # Optional user association
      user_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"))
      user: Mapped["User"] = relationship("User", back_populates="email_logs")
  ```

### 9. Email Rate Limiting and Throttling

- [ ] **Add email rate limiting**

  ```python
  # File: src/py/app/lib/email_rate_limiter.py
  class EmailRateLimiter:
      def __init__(self, redis_client, settings: EmailSettings):
          self.redis = redis_client
          self.settings = settings
      
      async def check_rate_limit(self, identifier: str) -> bool:
          """Check if email sending is rate limited"""
          
      async def increment_count(self, identifier: str) -> None:
          """Increment email count for rate limiting"""
          
      async def get_remaining_quota(self, identifier: str) -> int:
          """Get remaining email quota"""
  ```

## Frontend Tasks

### 1. Email Preferences Component

- [ ] **Create email preferences interface**

  ```tsx
  // File: src/js/src/components/settings/email-preferences.tsx
  interface EmailPreference {
    id: string;
    name: string;
    description: string;
    enabled: boolean;
    required: boolean;
  }
  
  export function EmailPreferences() {
    // Display email notification preferences
    // Toggle individual preferences
    // Show required vs optional emails
    // Save preferences to backend
  }
  ```

### 2. Email Verification Components

- [ ] **Create email verification status component**

  ```tsx
  // File: src/js/src/components/auth/email-verification-status.tsx
  interface EmailVerificationStatusProps {
    user: User;
    onResendVerification: () => Promise<void>;
  }
  
  export function EmailVerificationStatus({ 
    user, 
    onResendVerification 
  }: EmailVerificationStatusProps) {
    // Show verification status
    // Resend verification email button
    // Success/error states
  }
  ```

### 3. Email Testing Interface (Admin)

- [ ] **Create email testing interface for admins**

  ```tsx
  // File: src/js/src/components/admin/email-tester.tsx
  export function EmailTester() {
    // Select email template
    // Preview email with sample data
    // Send test email
    // View email logs and analytics
  }
  ```

## Testing

### 1. Backend Tests

- [ ] **Test EmailService**
  - Template rendering
  - Email sending (mocked)
  - Error handling
  - Rate limiting

- [ ] **Test email templates**
  - Template compilation
  - Context variable substitution
  - HTML/text rendering
  - Mobile responsiveness (via tools)

- [ ] **Test email providers**
  - SMTP provider
  - SendGrid provider
  - AWS SES provider
  - Provider fallback

- [ ] **Test email events**
  - Welcome email sending
  - Team invitation emails
  - Password reset emails
  - Event listener registration

### 2. Email Template Testing

- [ ] **Visual email testing**
  - Test across email clients (Litmus/Email on Acid)
  - Mobile responsiveness
  - Dark mode compatibility
  - Accessibility compliance

### 3. Integration Tests

- [ ] **Test email workflows**
  - User registration → welcome email
  - Team invitation → invitation email
  - Password reset → reset email
  - Email verification → verification email

## Configuration

### 1. Development Configuration

- [ ] **Local SMTP setup**

  ```bash
  # Use MailHog for local development
  docker run -d -p 1025:1025 -p 8025:8025 mailhog/mailhog
  
  # Environment variables
  SMTP_HOST=localhost
  SMTP_PORT=1025
  SMTP_USERNAME=""
  SMTP_PASSWORD=""
  SMTP_USE_TLS=false
  EMAIL_DEBUG=true
  ```

### 2. Production Configuration

- [ ] **Production email setup**

  ```bash
  # SendGrid configuration
  EMAIL_PROVIDER=sendgrid
  SENDGRID_API_KEY=your_sendgrid_api_key
  DEFAULT_FROM_EMAIL=noreply@yourdomain.com
  DEFAULT_FROM_NAME="Your App Name"
  
  # Or AWS SES configuration
  EMAIL_PROVIDER=ses
  AWS_SES_REGION=us-east-1
  AWS_ACCESS_KEY_ID=your_access_key
  AWS_SECRET_ACCESS_KEY=your_secret_key
  ```

### 3. Email Branding

- [ ] **Configure email branding**

  ```python
  # Add to settings
  APP_LOGO_URL: str = "https://yourdomain.com/logo.png"
  APP_NAME: str = "Your App Name"
  APP_URL: str = "https://yourdomain.com"
  SUPPORT_EMAIL: str = "support@yourdomain.com"
  ```

## Security Considerations

### 1. Email Content Security

- [ ] **Sanitize email content**
  - HTML sanitization
  - XSS prevention
  - Link validation
  - Attachment scanning

### 2. Anti-Spam Measures

- [ ] **Implement anti-spam features**
  - Rate limiting per user/IP
  - Bounce handling
  - Unsubscribe management
  - DMARC/SPF/DKIM configuration

### 3. Data Privacy

- [ ] **Email privacy compliance**
  - GDPR compliance for EU users
  - Data retention policies
  - Unsubscribe handling
  - Personal data in emails

## Monitoring and Analytics

### 1. Email Metrics

- [ ] **Track email performance**
  - Delivery rates
  - Open rates
  - Click rates
  - Bounce rates
  - Unsubscribe rates

### 2. Error Monitoring

- [ ] **Monitor email failures**
  - Failed deliveries
  - Provider errors
  - Template errors
  - Rate limit violations

### 3. Email Dashboard

- [ ] **Create email analytics dashboard**
  - Real-time email stats
  - Template performance
  - Provider status
  - Error rates and trends

## Documentation

### 1. Email Template Guide

- [ ] **Create template documentation**
  - Available templates
  - Context variables
  - Customization guide
  - Best practices

### 2. Email Provider Setup

- [ ] **Document provider setup**
  - SMTP configuration
  - SendGrid setup
  - AWS SES setup
  - DNS configuration (SPF/DKIM)

### 3. Email Testing Guide

- [ ] **Create testing documentation**
  - Local testing setup
  - Template testing
  - Email client testing
  - Performance testing

## Success Criteria

- [ ] All transactional emails working (welcome, verification, reset, invitations)
- [ ] Professional HTML email templates with mobile support
- [ ] Multiple email provider support (SMTP, SendGrid, SES)
- [ ] Event-driven email sending
- [ ] Background job processing for emails
- [ ] Email analytics and tracking
- [ ] Rate limiting and anti-spam measures
- [ ] Comprehensive testing suite
- [ ] Email preferences management
- [ ] Production-ready error handling and monitoring
