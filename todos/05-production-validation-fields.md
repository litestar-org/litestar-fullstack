# Production-Ready Field Validation

**Priority: HIGH** | **Effort: Medium** | **Phase: 1**
**Addresses GitHub Issue #180: Production-ready validation of fields like email and password**

## 📊 Implementation Status

### ✅ Backend Implementation: 70% Complete
- Core validation framework implemented
- Email validation with blocked domains and patterns
- Enhanced password validation with common password checking
- Name, username, URL, slug, and phone validation functions
- Schema integration with runtime validation
- Database fields added (username, phone)

### ❌ Frontend Implementation: 0% Complete
- No client-side validation components
- No real-time validation
- No password strength indicator

### ❌ Testing: 0% Complete
- No unit tests for validators
- No integration tests
- No end-to-end testing

### 🔧 Still Needed:
1. Install optional dependencies (email-validator, phonenumbers)
2. Frontend validation components
3. Comprehensive test coverage
4. Validation middleware
5. Custom validation decorators
6. Performance optimizations
7. Security hardening

## Overview
Implement comprehensive, security-minded validation for all user input fields using msgspec with custom validation. Focus on email addresses, passwords, and other critical fields with proper constraints, sanitization, and security checks.

## Backend Tasks

### 1. Core Validation Framework
- [ ] **Create validation utilities module**
  ```python
  # File: src/py/app/lib/validation.py
  import re
  import unicodedata
  from typing import Annotated, Any
  import msgspec
  from email_validator import validate_email, EmailNotValidError
  
  class ValidationError(Exception):
      """Custom validation error"""
      pass
  
  def validate_not_empty(value: str) -> str:
      """Ensure string is not empty after stripping"""
      cleaned = value.strip()
      if not cleaned:
          raise ValidationError("Value cannot be empty")
      return cleaned
  
  def validate_length(value: str, min_length: int = 0, max_length: int | None = None) -> str:
      """Validate string length"""
      if len(value) < min_length:
          raise ValidationError(f"Must be at least {min_length} characters")
      if max_length and len(value) > max_length:
          raise ValidationError(f"Must not exceed {max_length} characters")
      return value
  
  def validate_no_control_chars(value: str) -> str:
      """Remove/reject control characters"""
      if any(unicodedata.category(char) == 'Cc' for char in value if char not in '\n\r\t'):
          raise ValidationError("Contains invalid control characters")
      return value
  ```

### 2. Email Validation
- [ ] **Create production-ready email validation**
  ```python
  # Add to src/py/app/lib/validation.py
  class EmailStr(str):
      """Production-ready email validation with comprehensive checks"""
      
      # Blocked email patterns (disposable, suspicious, etc.)
      BLOCKED_DOMAINS = {
          '10minutemail.com', 'tempmail.org', 'guerrillamail.com',
          'mailinator.com', 'throwaway.email', 'temp-mail.org'
      }
      
      BLOCKED_PATTERNS = [
          r'.*\+.*test.*@.*',  # +test emails
          r'.*\+.*spam.*@.*',  # +spam emails
          r'^test.*@.*',       # emails starting with test
      ]
      
      @classmethod
      def __get_validators__(cls):
          yield cls.validate
      
      @classmethod
      def validate(cls, v: str) -> str:
          if not isinstance(v, str):
              raise ValidationError("Email must be a string")
          
          # Basic cleanup
          email = v.strip().lower()
          
          # Length check
          if len(email) > 254:  # RFC 5321 limit
              raise ValidationError("Email address too long")
          
          if len(email) < 3:
              raise ValidationError("Email address too short")
          
          # Use email-validator library for comprehensive validation
          try:
              validated_email = validate_email(
                  email,
                  check_deliverability=True,  # DNS MX record check
                  allow_smtputf8=False,       # ASCII only for compatibility
              )
              email = validated_email.email
          except EmailNotValidError as e:
              raise ValidationError(f"Invalid email address: {str(e)}")
          
          # Check against blocked domains
          domain = email.split('@')[1]
          if domain in cls.BLOCKED_DOMAINS:
              raise ValidationError("Email domain not allowed")
          
          # Check against blocked patterns
          for pattern in cls.BLOCKED_PATTERNS:
              if re.match(pattern, email):
                  raise ValidationError("Email format not allowed")
          
          # Additional security checks
          local_part = email.split('@')[0]
          if len(local_part) > 64:  # RFC 5321 limit
              raise ValidationError("Email local part too long")
          
          return email
  
  # Type annotation for use in schemas
  Email = Annotated[EmailStr, msgspec.Meta(description="Valid email address")]
  ```

### 3. Password Validation
- [ ] **Create comprehensive password validation**
  ```python
  # Add to src/py/app/lib/validation.py
  import hashlib
  import zxcvbn  # Password strength estimation
  
  class PasswordStr(str):
      """Production-ready password validation with security checks"""
      
      # Common passwords hash set (first 1000 most common)
      COMMON_PASSWORDS_HASHES = {
          # SHA256 hashes of common passwords
          'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',  # empty
          '5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8',  # 'password'
          '65e84be33532fb784c48129675f9eff3a682b27168c0ea744b2cf58ee02337c5',  # 'qwerty'
          # ... add more common password hashes
      }
      
      @classmethod
      def validate(cls, v: str) -> str:
          if not isinstance(v, str):
              raise ValidationError("Password must be a string")
          
          # Length requirements
          if len(v) < 12:
              raise ValidationError("Password must be at least 12 characters long")
          if len(v) > 128:
              raise ValidationError("Password must not exceed 128 characters")
          
          # Character requirements
          if not re.search(r'[A-Z]', v):
              raise ValidationError("Password must contain at least one uppercase letter")
          if not re.search(r'[a-z]', v):
              raise ValidationError("Password must contain at least one lowercase letter")
          if not re.search(r'\d', v):
              raise ValidationError("Password must contain at least one digit")
          if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
              raise ValidationError("Password must contain at least one special character")
          
          # Check against common passwords
          password_hash = hashlib.sha256(v.encode()).hexdigest()
          if password_hash in cls.COMMON_PASSWORDS_HASHES:
              raise ValidationError("Password is too common, please choose a different one")
          
          # Advanced strength check using zxcvbn
          strength = zxcvbn.zxcvbn(v)
          if strength['score'] < 2:  # 0-4 scale, require at least 2
              raise ValidationError(
                  f"Password is too weak: {strength['feedback']['warning'] or 'Please choose a stronger password'}"
              )
          
          # Check for personal information patterns (basic)
          if re.search(r'(password|123456|qwerty|admin)', v.lower()):
              raise ValidationError("Password contains common patterns")
          
          return v
  
  # Type annotation for use in schemas
  Password = Annotated[PasswordStr, msgspec.Meta(description="Strong password (12+ chars, mixed case, numbers, symbols)")]
  ```

### 4. Name and Text Validation
- [ ] **Create name validation**
  ```python
  # Add to src/py/app/lib/validation.py
  class NameStr(str):
      """Human name validation with proper handling of international names"""
      
      @classmethod
      def validate(cls, v: str) -> str:
          if not isinstance(v, str):
              raise ValidationError("Name must be a string")
          
          # Clean and normalize
          name = v.strip()
          name = re.sub(r'\s+', ' ', name)  # Normalize whitespace
          
          # Length validation
          if len(name) < 1:
              raise ValidationError("Name cannot be empty")
          if len(name) > 100:
              raise ValidationError("Name must not exceed 100 characters")
          
          # Character validation - allow letters, spaces, hyphens, apostrophes, periods
          if not re.match(r"^[a-zA-ZÀ-ÿ\u0100-\u017F\u0180-\u024F\u1E00-\u1EFF\s'\-\.]+$", name):
              raise ValidationError("Name contains invalid characters")
          
          # Prevent abuse patterns
          if re.search(r'(.)\1{4,}', name):  # 5+ repeated characters
              raise ValidationError("Name contains suspicious patterns")
          
          return name
  
  class UsernameStr(str):
      """Username validation with uniqueness and character restrictions"""
      
      RESERVED_USERNAMES = {
          'admin', 'root', 'api', 'www', 'mail', 'ftp', 'support',
          'help', 'security', 'privacy', 'terms', 'about', 'contact',
          'blog', 'news', 'app', 'application', 'system', 'test'
      }
      
      @classmethod
      def validate(cls, v: str) -> str:
          if not isinstance(v, str):
              raise ValidationError("Username must be a string")
          
          # Clean and normalize
          username = v.strip().lower()
          
          # Length validation
          if len(username) < 3:
              raise ValidationError("Username must be at least 3 characters")
          if len(username) > 30:
              raise ValidationError("Username must not exceed 30 characters")
          
          # Character validation - alphanumeric, hyphens, underscores only
          if not re.match(r'^[a-z0-9_-]+$', username):
              raise ValidationError("Username can only contain letters, numbers, hyphens, and underscores")
          
          # Must start with letter or number
          if not re.match(r'^[a-z0-9]', username):
              raise ValidationError("Username must start with a letter or number")
          
          # Check reserved usernames
          if username in cls.RESERVED_USERNAMES:
              raise ValidationError("Username is reserved and cannot be used")
          
          # Prevent abuse patterns
          if re.search(r'(.)\1{3,}', username):  # 4+ repeated characters
              raise ValidationError("Username contains too many repeated characters")
          
          return username
  
  # Type annotations
  Name = Annotated[NameStr, msgspec.Meta(description="Human name (1-100 characters, letters/spaces/hyphens only)")]
  Username = Annotated[UsernameStr, msgspec.Meta(description="Username (3-30 characters, alphanumeric/hyphens/underscores)")]
  ```

### 5. URL and Slug Validation
- [ ] **Create URL and slug validation**
  ```python
  # Add to src/py/app/lib/validation.py
  from urllib.parse import urlparse
  
  class UrlStr(str):
      """URL validation with security checks"""
      
      ALLOWED_SCHEMES = {'http', 'https'}
      BLOCKED_DOMAINS = {'localhost', '127.0.0.1', '0.0.0.0'}
      
      @classmethod
      def validate(cls, v: str) -> str:
          if not isinstance(v, str):
              raise ValidationError("URL must be a string")
          
          url = v.strip()
          
          # Length check
          if len(url) > 2048:
              raise ValidationError("URL too long")
          
          try:
              parsed = urlparse(url)
          except Exception:
              raise ValidationError("Invalid URL format")
          
          # Scheme validation
          if parsed.scheme not in cls.ALLOWED_SCHEMES:
              raise ValidationError(f"URL scheme must be one of: {', '.join(cls.ALLOWED_SCHEMES)}")
          
          # Domain validation
          if parsed.hostname in cls.BLOCKED_DOMAINS:
              raise ValidationError("URL domain not allowed")
          
          # Prevent common attacks
          if any(suspicious in url.lower() for suspicious in ['javascript:', 'data:', 'vbscript:']):
              raise ValidationError("URL contains suspicious content")
          
          return url
  
  class SlugStr(str):
      """Slug validation for URL-safe identifiers"""
      
      @classmethod
      def validate(cls, v: str) -> str:
          if not isinstance(v, str):
              raise ValidationError("Slug must be a string")
          
          slug = v.strip().lower()
          
          # Length validation
          if len(slug) < 1:
              raise ValidationError("Slug cannot be empty")
          if len(slug) > 100:
              raise ValidationError("Slug must not exceed 100 characters")
          
          # Character validation - lowercase, numbers, hyphens only
          if not re.match(r'^[a-z0-9-]+$', slug):
              raise ValidationError("Slug can only contain lowercase letters, numbers, and hyphens")
          
          # Cannot start or end with hyphen
          if slug.startswith('-') or slug.endswith('-'):
              raise ValidationError("Slug cannot start or end with a hyphen")
          
          # Cannot have consecutive hyphens
          if '--' in slug:
              raise ValidationError("Slug cannot contain consecutive hyphens")
          
          return slug
  
  # Type annotations
  Url = Annotated[UrlStr, msgspec.Meta(description="Valid HTTP/HTTPS URL")]
  Slug = Annotated[SlugStr, msgspec.Meta(description="URL-safe slug (lowercase, alphanumeric, hyphens)")]
  ```

### 6. Phone and Address Validation
- [ ] **Create phone number validation**
  ```python
  # Add to src/py/app/lib/validation.py
  import phonenumbers
  from phonenumbers import NumberParseException
  
  class PhoneStr(str):
      """International phone number validation"""
      
      @classmethod
      def validate(cls, v: str) -> str:
          if not isinstance(v, str):
              raise ValidationError("Phone number must be a string")
          
          phone = v.strip()
          
          if not phone:
              raise ValidationError("Phone number cannot be empty")
          
          try:
              parsed_number = phonenumbers.parse(phone, None)
              if not phonenumbers.is_valid_number(parsed_number):
                  raise ValidationError("Invalid phone number")
              
              # Format to international format
              formatted = phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.E164)
              return formatted
              
          except NumberParseException:
              raise ValidationError("Invalid phone number format")
  
  # Type annotation
  Phone = Annotated[PhoneStr, msgspec.Meta(description="Valid international phone number")]
  ```

### 7. Update Existing Schemas
- [ ] **Update user schemas with new validation**
  ```python
  # Update: src/py/app/schemas/accounts.py
  from app.lib.validation import Email, Password, Name, Username, Phone
  
  @dataclass
  class UserCreate(msgspec.Struct):
      email: Email
      password: Password
      name: Name | None = None
      username: Username | None = None
      phone: Phone | None = None
      
      # Additional validation in post_init
      def __post_init__(self):
          # Custom cross-field validation
          if self.username and self.username == self.email.split('@')[0]:
              raise ValueError("Username cannot be the same as email local part")
  
  @dataclass
  class UserUpdate(msgspec.Struct):
      name: Name | None = None
      username: Username | None = None
      phone: Phone | None = None
      # Note: email and password updates handled separately for security
      
      def __post_init__(self):
          # Ensure at least one field is provided
          if not any([self.name, self.username, self.phone]):
              raise ValueError("At least one field must be provided for update")
  
  @dataclass
  class AccountLogin(msgspec.Struct):
      username: Email  # Use email for login
      password: str = msgspec.field(min_length=1, max_length=128)  # Don't validate password strength on login
  ```

### 8. Validation Middleware
- [ ] **Create validation error handler**
  ```python
  # File: src/py/app/lib/validation_middleware.py
  from litestar import Request, Response
  from litestar.exceptions import ValidationException
  from litestar.middleware.base import AbstractMiddleware
  
  class ValidationMiddleware(AbstractMiddleware):
      """Middleware to handle validation errors consistently"""
      
      async def call_next(self, request: Request) -> Response:
          try:
              return await self.app(request.scope, request.receive, request.send)
          except ValidationError as e:
              # Convert our custom validation errors to Litestar format
              raise ValidationException(detail=str(e))
          except ValueError as e:
              # Handle msgspec validation errors
              if "validation" in str(e).lower():
                  raise ValidationException(detail=str(e))
              raise
  ```

### 9. Custom Validation Decorators
- [ ] **Create validation decorators for services**
  ```python
  # File: src/py/app/lib/validation_decorators.py
  from functools import wraps
  from typing import Callable, Any
  
  def validate_input(validation_func: Callable[[Any], Any]):
      """Decorator to validate service method inputs"""
      def decorator(func: Callable) -> Callable:
          @wraps(func)
          async def wrapper(*args, **kwargs):
              # Apply validation to specified arguments
              for arg_name, arg_value in kwargs.items():
                  if hasattr(validation_func, arg_name):
                      kwargs[arg_name] = getattr(validation_func, arg_name)(arg_value)
              return await func(*args, **kwargs)
          return wrapper
      return decorator
  
  def sanitize_html(func: Callable) -> Callable:
      """Decorator to sanitize HTML in string arguments"""
      @wraps(func)
      async def wrapper(*args, **kwargs):
          import bleach
          for key, value in kwargs.items():
              if isinstance(value, str) and any(char in value for char in '<>&"\''):
                  kwargs[key] = bleach.clean(value, tags=[], strip=True)
          return await func(*args, **kwargs)
      return wrapper
  ```

## Frontend Tasks

### 1. Client-Side Validation Components
- [ ] **Create validation hook**
  ```tsx
  // File: src/js/src/hooks/use-validation.ts
  interface ValidationRule {
    required?: boolean;
    minLength?: number;
    maxLength?: number;
    pattern?: RegExp;
    custom?: (value: any) => string | null;
  }
  
  interface ValidationRules {
    [field: string]: ValidationRule;
  }
  
  export function useValidation<T extends Record<string, any>>(
    data: T,
    rules: ValidationRules
  ) {
    const [errors, setErrors] = useState<Record<string, string>>({});
    
    const validate = useCallback((field?: string) => {
      // Validation logic
    }, [data, rules]);
    
    const isValid = Object.keys(errors).length === 0;
    
    return { errors, validate, isValid };
  }
  ```

### 2. Enhanced Form Components
- [ ] **Create validated input components**
  ```tsx
  // File: src/js/src/components/ui/validated-input.tsx
  interface ValidatedInputProps extends InputHTMLAttributes<HTMLInputElement> {
    label: string;
    error?: string;
    validationRules?: ValidationRule;
    showStrength?: boolean; // For passwords
  }
  
  export function ValidatedInput({
    label,
    error,
    validationRules,
    showStrength = false,
    ...props
  }: ValidatedInputProps) {
    const [localError, setLocalError] = useState<string>('');
    const [strength, setStrength] = useState<PasswordStrength | null>(null);
    
    // Real-time validation
    // Password strength indicator
    // Error display
    // Accessibility features
  }
  ```

### 3. Password Strength Component
- [ ] **Create password strength indicator**
  ```tsx
  // File: src/js/src/components/ui/password-strength.tsx
  interface PasswordStrengthProps {
    password: string;
    requirements?: PasswordRequirement[];
  }
  
  export function PasswordStrength({ password, requirements }: PasswordStrengthProps) {
    const strength = calculatePasswordStrength(password);
    
    return (
      <div className="space-y-2">
        {/* Strength meter */}
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div 
            className={`h-2 rounded-full transition-all ${getStrengthColor(strength)}`}
            style={{ width: `${(strength.score / 4) * 100}%` }}
          />
        </div>
        
        {/* Requirements checklist */}
        <div className="space-y-1">
          {requirements?.map((req) => (
            <div key={req.id} className={`flex items-center space-x-2 text-sm ${
              req.met ? 'text-green-600' : 'text-gray-500'
            }`}>
              <CheckIcon className={`h-4 w-4 ${req.met ? 'text-green-600' : 'text-gray-300'}`} />
              <span>{req.description}</span>
            </div>
          ))}
        </div>
      </div>
    );
  }
  ```

### 4. Real-time Validation
- [ ] **Create real-time validation utilities**
  ```tsx
  // File: src/js/src/lib/validation/real-time.ts
  export const validateEmail = (email: string): string | null => {
    if (!email) return null;
    
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      return 'Please enter a valid email address';
    }
    
    // Check against blocked domains
    const domain = email.split('@')[1];
    if (BLOCKED_DOMAINS.includes(domain)) {
      return 'This email domain is not allowed';
    }
    
    return null;
  };
  
  export const validatePassword = (password: string): PasswordValidation => {
    return {
      length: password.length >= 12,
      uppercase: /[A-Z]/.test(password),
      lowercase: /[a-z]/.test(password),
      number: /\d/.test(password),
      special: /[!@#$%^&*(),.?":{}|<>]/.test(password),
      strength: calculateStrength(password)
    };
  };
  ```

## Testing

### 1. Backend Validation Tests
- [ ] **Test email validation**
  - Valid email formats
  - Invalid email formats
  - Blocked domains and patterns
  - Edge cases (long emails, special characters)
  - Internationalization

- [ ] **Test password validation**
  - Strength requirements
  - Common password detection
  - Character requirements
  - Length limits
  - Security patterns

- [ ] **Test other field validation**
  - Name validation (international characters)
  - Username validation (reserved names, patterns)
  - Phone number validation (international formats)
  - URL validation (security checks)

### 2. Frontend Validation Tests
- [ ] **Test validation components**
  - Real-time validation
  - Error display
  - Strength indicators
  - Accessibility

- [ ] **Test validation hooks**
  - Field validation
  - Form validation
  - Error state management

### 3. Integration Tests
- [ ] **Test end-to-end validation**
  - Frontend validation → backend validation
  - Error handling consistency
  - User experience flows

## Security Considerations

### 1. Input Sanitization
- [ ] **Implement comprehensive sanitization**
  - HTML tag stripping
  - Script injection prevention
  - SQL injection prevention
  - Control character removal

### 2. Rate Limiting
- [ ] **Add validation rate limiting**
  - Prevent brute force validation attempts
  - Limit email validation requests
  - Throttle username availability checks

### 3. Error Information Disclosure
- [ ] **Prevent information leakage**
  - Generic error messages where appropriate
  - No exposure of internal validation logic
  - Consistent error response timing

## Performance Considerations

### 1. Validation Optimization
- [ ] **Optimize validation performance**
  - Cache compiled regex patterns
  - Optimize common password checking
  - Efficient blocked domain lookups
  - Debounce real-time validation

### 2. Database Validation
- [ ] **Add database constraints**
  - Email uniqueness constraints
  - Username uniqueness constraints
  - Check constraints for valid formats
  - Indexes for validation queries

## Documentation

### 1. Validation Rules Documentation
- [ ] **Document all validation rules**
  - Field requirements
  - Error messages
  - Security rationale
  - Examples and edge cases

### 2. Developer Guide
- [ ] **Create validation developer guide**
  - How to add new validators
  - Custom validation patterns
  - Frontend/backend consistency
  - Testing validation rules

## Success Criteria
- [ ] All critical fields have production-ready validation
- [ ] Email validation includes deliverability checks
- [ ] Password validation enforces strong security
- [ ] Client-side validation matches backend validation
- [ ] Real-time validation provides good UX
- [ ] Comprehensive error handling and messaging
- [ ] Performance optimized validation
- [ ] Security-focused validation prevents common attacks
- [ ] International character support where appropriate
- [ ] 100% test coverage for validation logic