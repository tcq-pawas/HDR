# Role-Based Authentication and Dashboard System

This document describes the comprehensive role-based authentication and dashboard system implemented for the HeyDay Realty Django application.

## Overview

The system implements **strict role-based access control** using Django Groups (`admin`, `investor`, `customer`) with automatic redirection to role-specific dashboards and complete data isolation between user roles.

## Key Features

### 🔐 **Strict Access Control**
- **Role-based dashboard access**: Users can only access their designated dashboard
- **Cross-role prevention**: Admin cannot access investor/customer dashboards, and vice versa
- **API protection**: All API endpoints are protected with role validation
- **Automatic redirection**: `/dashboard/` acts as a universal entry point that redirects based on user role

### 🏗️ **Architecture Components**

#### 1. Authentication Utilities (`Apps.Administration.auth_utils`)
- `get_user_role(user)`: Determines user's primary role from group membership
- `assign_user_group(user, role)`: Assigns user to appropriate group
- `role_required(allowed_roles)`: Decorator for role-based view protection
- `get_role_based_redirect_url(user)`: Returns appropriate dashboard URL
- `RoleRequiredMixin`: Mixin for class-based view protection

#### 2. Smart Dashboard System (`Apps.Administration.smart_dashboard_views`)
- `SmartDashboardRedirectView`: Universal dashboard entry point
- `RoleBasedDashboardMixin`: Base mixin for dashboard access control
- `AdminDashboardMixin`: Admin-only access mixin
- `CustomerDashboardMixin`: Customer-only access mixin
- `InvestorDashboardMixin`: Investor-only access mixin

#### 3. Authentication Views (`Apps.Administration.auth_views`)
- `CustomLoginView`: Role-aware login with automatic redirection
- `CustomLogoutView`: Role-aware logout
- `RoleBasedDashboardView`: Base view for role-specific dashboards

## User Roles and Permissions

### 👨‍💼 **Admin Role**
- **Dashboard**: `/admin-dashboard/dashboard/`
- **Access**: Complete system-level insights and management
- **Features**:
  - Total users, customers, investors, properties statistics
  - Sales analytics and revenue metrics
  - Property analytics and performance tracking
  - User management and role assignment
  - System settings and configuration
  - Activity logs and monitoring
  - Report generation and management

### 💼 **Investor Role**
- **Dashboard**: `/investor/dashboard/`
- **Access**: Investment-specific data and portfolio management
- **Features**:
  - Personal investment portfolio analysis
  - ROI tracking and returns analysis
  - Investment performance trends
  - Available investment opportunities
  - Document management
  - Investment milestones and important dates
  - Sold vs remaining units analysis

### 🏠 **Customer Role**
- **Dashboard**: `/customer/dashboard/`
- **Access**: Personal property data and purchase history
- **Features**:
  - Personal purchase statistics
  - Owned properties and details
  - Property interests and preferences
  - Location and budget analysis
  - Activity timeline
  - Recommended properties based on preferences
  - Document management

## URL Structure

### Universal Entry Point
```
/dashboard/ → SmartDashboardRedirectView → Role-specific dashboard
```

### Role-Specific Dashboards
```
/admin-dashboard/dashboard/    → Admin Dashboard (Admin only)
/investor/dashboard/           → Investor Dashboard (Investor only)  
/customer/dashboard/           → Customer Dashboard (Customer only)
```

### Authentication
```
/auth/login/                   → CustomLoginView
/auth/logout/                  → CustomLogoutView
/auth/unauthorized/            → Unauthorized access page
```

## Implementation Details

### Role Detection Logic
```python
def get_user_role(user):
    """Get the primary role of a user based on their group membership"""
    if not user.is_authenticated:
        return None
    
    # Priority: admin > investor > customer
    if user.is_superuser or user.groups.filter(name='admin').exists():
        return 'admin'
    elif user.groups.filter(name='investor').exists():
        return 'investor'
    elif user.groups.filter(name='customer').exists():
        return 'customer'
    else:
        return None
```

### Dashboard Access Control
```python
class RoleBasedDashboardMixin:
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('auth:login')
        
        user_role = get_user_role(request.user)
        if not user_role:
            return redirect('auth:unauthorized')
        
        if not self.has_role_access(user_role):
            raise PermissionDenied("Access denied")
        
        return super().dispatch(request, *args, **kwargs)
```

### API Protection
```python
class AdminProfileView(generics.RetrieveUpdateAPIView):
    def get_object(self):
        # Only admin users can access admin profiles
        if get_user_role(self.request.user) != 'admin':
            raise PermissionDenied("Admin access required.")
        
        profile, created = AdminProfile.objects.get_or_create(user=self.request.user)
        return profile
```

## Security Features

### 🔒 **Strict Authorization**
- All dashboard views use role-specific mixins
- API endpoints validate user role before processing
- Cross-role access attempts result in 403 Forbidden
- Unassigned users are redirected to unauthorized page

### 🛡️ **Data Isolation**
- Admin sees system-wide data only
- Investors see only their investment data
- Customers see only their personal data
- No data leakage between roles

### 🔄 **Automatic Redirection**
- Login automatically redirects to appropriate dashboard
- `/dashboard/` acts as smart entry point
- Unauthorized access attempts are logged and blocked

## Testing

The system includes comprehensive tests in `test_role_based_access.py`:

### Automated Tests
- User role detection
- Role-based redirect URLs
- Dashboard access control
- API access control
- Authentication redirects
- Role permission functions
- Group assignment
- Dashboard data isolation

### Manual Scenarios
- Admin accessing investor dashboard (should fail)
- Investor accessing customer dashboard (should fail)
- Customer accessing admin dashboard (should fail)
- Unassigned user accessing any dashboard (should redirect)

## Usage Examples

### Creating Users with Roles
```python
from Apps.Administration.auth_utils import create_user_with_role

# Create admin user
admin = create_user_with_role(
    username='admin_user',
    email='admin@example.com',
    password='securepass',
    role='admin'
)

# Create investor user
investor = create_user_with_role(
    username='investor_user',
    email='investor@example.com',
    password='securepass',
    role='investor'
)

# Create customer user
customer = create_user_with_role(
    username='customer_user',
    email='customer@example.com',
    password='securepass',
    role='customer'
)
```

### Protecting Views
```python
# Function-based view
@role_required(['admin', 'investor'])
def sensitive_view(request):
    # Only admin and investor users can access
    pass

# Class-based view
class AdminOnlyView(AdminDashboardMixin, TemplateView):
    # Only admin users can access
    pass
```

### Checking User Roles
```python
from Apps.Administration.auth_utils import get_user_role, has_role_permission

def my_view(request):
    user_role = get_user_role(request.user)
    
    if user_role == 'admin':
        # Admin-specific logic
        pass
    elif user_role == 'investor':
        # Investor-specific logic
        pass
    
    # Check specific role permission
    if has_role_permission(request.user, 'admin'):
        # User has admin permissions
        pass
```

## Migration and Setup

### 1. Create Django Groups
```python
# Run in Django shell or migration
from django.contrib.auth.models import Group

Group.objects.get_or_create(name='admin')
Group.objects.get_or_create(name='investor')
Group.objects.get_or_create(name='customer')
```

### 2. Assign Existing Users
```python
from Apps.Administration.auth_utils import assign_user_group

# Assign existing users to appropriate groups
for user in User.objects.all():
    # Logic to determine user's role
    if user.is_staff:
        assign_user_group(user, 'admin')
    elif hasattr(user, 'investor_profile'):
        assign_user_group(user, 'investor')
    elif hasattr(user, 'customer_profile'):
        assign_user_group(user, 'customer')
```

### 3. Update Templates
Update login forms and navigation to use new URL patterns:
```html
<!-- Login form -->
<form action="{% url 'auth:login' %}" method="post">

<!-- Dashboard links -->
<a href="{% url 'admin_dash:dashboard' %}">Admin Dashboard</a>
<a href="{% url 'investor:dashboard' %}">Investor Dashboard</a>
<a href="{% url 'customer:dashboard' %}">Customer Dashboard</a>
```

## Troubleshooting

### Common Issues

#### 1. Users Getting "Unauthorized" Access
- **Cause**: User is not assigned to any role group
- **Solution**: Assign user to appropriate group using `assign_user_group()`

#### 2. Cross-Role Access Working
- **Cause**: Views not using role-specific mixins
- **Solution**: Ensure all dashboard views inherit from appropriate mixins

#### 3. API Endpoints Not Protected
- **Cause**: Missing role validation in API views
- **Solution**: Add role checks in API view methods

#### 4. Incorrect Redirection
- **Cause**: URL patterns not configured correctly
- **Solution**: Verify URL patterns and namespace configuration

### Debug Mode
Add logging to track role detection and access:
```python
import logging
logger = logging.getLogger(__name__)

def get_user_role(user):
    role = # ... role detection logic
    logger.info(f"User {user.username} detected role: {role}")
    return role
```

## Performance Considerations

### Database Optimization
- Use `select_related()` and `prefetch_related()` for profile queries
- Cache role information for authenticated users
- Optimize group membership queries

### Security Optimization
- Implement rate limiting for login attempts
- Cache user permissions for session duration
- Monitor and log unauthorized access attempts

## Future Enhancements

### Potential Improvements
1. **Multi-role support**: Allow users to have multiple roles
2. **Permission-based access**: Fine-grained permissions within roles
3. **Session management**: Enhanced session security and timeout
4. **Audit logging**: Comprehensive access logging
5. **API rate limiting**: Role-based API rate limiting

### Scalability
1. **Redis caching**: Cache role information and permissions
2. **Database indexing**: Optimize group membership queries
3. **Load balancing**: Distribute authentication load
4. **Microservices**: Separate authentication service

## Conclusion

This role-based authentication system provides:
- ✅ **Secure access control** with strict role separation
- ✅ **Automatic redirection** based on user roles
- ✅ **Complete data isolation** between user types
- ✅ **Scalable architecture** for future enhancements
- ✅ **Comprehensive testing** for reliability

The system ensures that users can only access their designated dashboards and data, providing a secure and scalable foundation for the HeyDay Realty application.
