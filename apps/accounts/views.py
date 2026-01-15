from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.urls import reverse
from django.views.generic import ListView
from django.db.models import Count, Q
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from datetime import datetime, time
from .models import LibraryUser, StudyRoom, StudyRoomBooking
from .forms import LibraryUserCreationForm, LibraryUserChangeForm
from apps.catalog.models import Book, Genre
from apps.events.models import Event
from apps.repository.models import Document
from django.apps import apps as django_apps

# Safe dynamic lookup for BlogPost
try:
    BlogPost = django_apps.get_model('blog', 'BlogPost')
except (LookupError, ModuleNotFoundError):
    BlogPost = None


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            next_url = request.GET.get('next', reverse('accounts:dashboard'))
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, 'accounts/login.html')


def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('home')  # Assuming there's a home view


def register_view(request):
    """Public registration page - now shows options for different registration types."""
    return render(request, 'accounts/register.html')


def student_register_view(request):
    """Student-specific registration view."""
    if request.method == 'POST':
        form = LibraryUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.membership_type = 'student'
            user.save()

            # Students are active immediately
            login(request, user)
            messages.success(request, 'Student registration successful! Welcome to Ramat Library.')
            return redirect('accounts:dashboard')
    else:
        form = LibraryUserCreationForm()

    return render(request, 'accounts/register_student.html', {'form': form})


def staff_register_view(request):
    """Staff-specific registration view."""
    if request.method == 'POST':
        form = LibraryUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.membership_type = 'staff'
            user.save()

            # Staff registration requires approval
            user.is_active = False  # Deactivate until approved
            user.save()
            # Send email to admin
            try:
                send_mail(
                    subject=f"New Staff Registration Requires Approval: {user.get_full_name()}",
                    message=f"A new staff member has registered and requires approval.\n\n"
                           f"Name: {user.get_full_name()}\n"
                           f"Username: {user.username}\n"
                           f"Email: {user.email}\n\n"
                           f"Please review and approve/reject this registration in the admin dashboard.",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[settings.EMAIL_HOST_USER],  # Send to admin email (piloteaglecrown@gmail.com)
                    fail_silently=False,
                )
                messages.success(request, 'Staff registration submitted successfully. Admin has been notified.')
            except Exception as e:
                # Log error and show user-friendly message
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Failed to send admin notification email for user {user.username}: {e}")
                messages.warning(request, 'Staff registration submitted, but email notification to admin failed. Please contact admin directly.')

            messages.info(request, 'Staff registration submitted for approval. You will receive an email notification once your account is activated.')
            return redirect('accounts:login')
    else:
        form = LibraryUserCreationForm()

    return render(request, 'accounts/register_staff.html', {'form': form})


@login_required
def dashboard_view(request):
    user = request.user

    # Redirect based on user role
    if user.is_superuser:
        return redirect('accounts:admin_dashboard')
    elif user.membership_type == 'staff' and user.is_staff_approved:
        return redirect('circulation:staff_dashboard')
    else:
        # Patron dashboard
        context = {
            'user': user,
            'current_loans': user.loans.filter(status='active')[:5],  # Show recent loans
            'reservations': user.reservations.filter(status='active')[:5],
            'recent_fines': user.loans.filter(fines__status='unpaid').distinct()[:5],
        }
        return render(request, 'accounts/dashboard.html', context)


@login_required
@user_passes_test(lambda u: u.is_superuser)
def admin_dashboard(request):
    """Comprehensive admin dashboard with full CRUD functionality for all models."""
    from django.apps import apps as django_apps
    from django.core.paginator import Paginator
    from django.db.models import Q
    from django.forms import modelform_factory

    # Handle CRUD operations
    if request.method == 'POST':
        action = request.POST.get('action')
        app_label = request.POST.get('app_label')
        model_name = request.POST.get('model_name')
        item_id = request.POST.get('item_id')

        try:
            model_class = django_apps.get_model(app_label, model_name)

            if action == 'delete':
                item = get_object_or_404(model_class, id=item_id)
                display_name = str(item)
                item.delete()
                messages.success(request, f'{model_class._meta.verbose_name} "{display_name}" has been deleted successfully.')
                return redirect('accounts:admin_dashboard')

            elif action == 'bulk_delete':
                ids = request.POST.getlist('selected_items')
                if ids:
                    # Attempt bulk deletion - let Django handle integrity constraints
                    try:
                        count = model_class.objects.filter(id__in=ids).delete()[0]
                        messages.success(request, f'{count} {model_class._meta.verbose_name_plural.lower()} deleted successfully.')
                    except Exception as e:
                        # Handle specific database integrity errors
                        error_message = str(e)
                        if 'foreign key constraint' in error_message.lower() or 'integrity constraint' in error_message.lower():
                            messages.error(request, f'Cannot delete selected {model_class._meta.verbose_name_plural.lower()} because some are referenced by other records. Please remove the related data first.')
                        else:
                            messages.error(request, f'Error deleting {model_class._meta.verbose_name_plural.lower()}: {error_message}')
                return redirect('accounts:admin_dashboard')

            elif action in ['create', 'edit']:
                # Handle create/edit forms
                try:
                    # Use a more flexible approach for form creation
                    exclude_fields = []
                    model_fields = [f.name for f in model_class._meta.get_fields() if not f.many_to_many]

                    # Exclude complex fields that might cause issues
                    for field in model_class._meta.get_fields():
                        if field.many_to_many or field.one_to_many:
                            exclude_fields.append(field.name)
                        elif hasattr(field, 'related_model') and field.related_model == model_class:
                            # Self-referencing fields can be problematic
                            exclude_fields.append(field.name)

                    # For now, use a basic set of fields to avoid complex relationships
                    if model_name in ['LibraryUser', 'Book', 'BookCopy', 'Author', 'Publisher']:
                        # Use specific fields for known models
                        if model_name == 'LibraryUser':
                            FormClass = LibraryUserChangeForm
                        else:
                            FormClass = modelform_factory(model_class, exclude=exclude_fields)
                    else:
                        # For other models, try to exclude problematic fields
                        FormClass = modelform_factory(model_class, exclude=exclude_fields)

                    if action == 'edit':
                        instance = get_object_or_404(model_class, id=item_id)
                        form = FormClass(request.POST, request.FILES, instance=instance)
                    else:
                        form = FormClass(request.POST, request.FILES)

                    if form.is_valid():
                        obj = form.save()
                        action_text = 'created' if action == 'create' else 'updated'
                        messages.success(request, f'{model_class._meta.verbose_name} "{str(obj)}" has been {action_text} successfully.')
                        return redirect('accounts:admin_dashboard')
                    else:
                        messages.error(request, f'Error saving {model_class._meta.verbose_name}: {form.errors}')
                        return redirect('accounts:admin_dashboard')

                except Exception as form_error:
                    messages.error(request, f'Error creating form for {model_name}: {str(form_error)}')
                    return redirect('accounts:admin_dashboard')

        except Exception as e:
            messages.error(request, f'Error performing action: {str(e)}')
            return redirect('accounts:admin_dashboard')

    # Pending staff approvals
    pending_staff = LibraryUser.objects.filter(
        membership_type='staff',
        is_staff_approved=False,
        is_active=False
    )

    # Recent user registrations
    recent_users = LibraryUser.objects.order_by('-date_joined')[:10]

    # User statistics
    total_users = LibraryUser.objects.count()
    active_users = LibraryUser.objects.filter(is_active=True).count()
    staff_users = LibraryUser.objects.filter(membership_type='staff', is_staff_approved=True).count()
    faculty_users = LibraryUser.objects.filter(membership_type='faculty').count()
    student_users = LibraryUser.objects.filter(membership_type='student').count()

    # System stats
    from apps.catalog.models import Book
    from apps.circulation.models import Loan, Reservation, Fine
    from apps.repository.models import Document
    from apps.events.models import Event
    total_books = Book.objects.active().count()
    document_count = Document.objects.count()
    event_count = Event.objects.count()
    active_loans = Loan.objects.filter(status='active').count()
    overdue_loans = Loan.objects.filter(status='active', due_date__lt=timezone.now().date()).count()
    pending_reservations = Reservation.objects.filter(status='pending').count()

    # System status
    storage_usage = "65%"  # Mock value - could calculate actual storage usage

    # Recent activity (enhanced with actual data)
    recent_actions = []
    try:
        # Recent user registrations
        for user in LibraryUser.objects.order_by('-date_joined')[:3]:
            recent_actions.append({
                'description': f'New user registered: {user.get_full_name()}',
                'timestamp': user.date_joined,
                'get_admin_url': reverse('admin:accounts_libraryuser_change', args=[user.id]),
                'get_icon': 'person-plus'
            })

        # Recent loans
        for loan in Loan.objects.order_by('-created_at')[:2]:
            recent_actions.append({
                'description': f'Book loan: {loan.book_copy.book.title[:30]}...',
                'timestamp': loan.created_at,
                'get_admin_url': reverse('admin:circulation_loan_change', args=[loan.id]),
                'get_icon': 'book'
            })

        # Recent documents
        for doc in Document.objects.order_by('-upload_date')[:2]:
            recent_actions.append({
                'description': f'Document uploaded: {doc.title[:30]}...',
                'timestamp': doc.upload_date,
                'get_admin_url': reverse('admin:repository_document_change', args=[doc.id]),
                'get_icon': 'file-earmark'
            })
    except:
        # Fallback to mock data
        recent_actions = [
            {'description': 'New user registered', 'timestamp': timezone.now() - timezone.timedelta(minutes=15), 'get_admin_url': '#', 'get_icon': 'person-plus'},
            {'description': 'Book loan processed', 'timestamp': timezone.now() - timezone.timedelta(hours=1), 'get_admin_url': '#', 'get_icon': 'book'},
        ]

    # Import all models for comprehensive management
    from apps.blog.models import BlogPost, StaticPage, FeaturedContent, News
    from apps.catalog.models import Author, Publisher, Faculty, Department, Topic, Genre, BookCopy
    from apps.circulation.models import Reservation, Fine, LoanRequest, Attendance
    from apps.events.models import Event, EventRegistration
    from apps.repository.models import Collection, Document

    # Get search and pagination parameters
    search_query = request.GET.get('search', '')
    page_number = request.GET.get('page', 1)
    items_per_page = 10

    # Build app list with full CRUD data
    app_list = []

    # Helper function to get admin actions
    def get_admin_actions(admin_class):
        """Extract custom actions from admin class."""
        actions = []
        if hasattr(admin_class, 'actions'):
            for action in admin_class.actions:
                if action != 'delete_selected':  # Skip default delete action
                    action_method = getattr(admin_class, action, None)
                    if action_method and hasattr(action_method, 'short_description'):
                        actions.append({
                            'name': action,
                            'description': action_method.short_description,
                            'method': action_method
                        })
        return actions

    # Accounts app
    from .admin import LibraryUserAdmin, StudyRoomAdmin, StudyRoomBookingAdmin
    accounts_models = [
        {
            'name': 'Library Users',
            'object_name': 'LibraryUser',
            'count': LibraryUser.objects.count(),
            'admin_url': reverse('admin:accounts_libraryuser_changelist'),
            'add_url': reverse('admin:accounts_libraryuser_add'),
            'icon': 'people',
            'fields': ['username', 'first_name', 'last_name', 'email', 'membership_type', 'is_active'],
            'actions': get_admin_actions(LibraryUserAdmin),
            'items': _get_paginated_items(LibraryUser, search_query, page_number, items_per_page, ['username', 'first_name', 'last_name', 'email'])
        },
        {
            'name': 'Study Rooms',
            'object_name': 'StudyRoom',
            'count': StudyRoom.objects.count(),
            'admin_url': reverse('admin:accounts_studyroom_changelist'),
            'add_url': reverse('admin:accounts_studyroom_add'),
            'icon': 'house-door',
            'fields': ['name', 'room_type', 'capacity', 'is_active'],
            'actions': get_admin_actions(StudyRoomAdmin),
            'items': _get_paginated_items(StudyRoom, search_query, page_number, items_per_page, ['name', 'room_type'])
        },
        {
            'name': 'Study Room Bookings',
            'object_name': 'StudyRoomBooking',
            'count': StudyRoomBooking.objects.count(),
            'admin_url': reverse('admin:accounts_studyroombooking_changelist'),
            'add_url': reverse('admin:accounts_studyroombooking_add'),
            'icon': 'calendar-check',
            'fields': ['user', 'room', 'date', 'status'],
            'actions': get_admin_actions(StudyRoomBookingAdmin),
            'items': _get_paginated_items(StudyRoomBooking, search_query, page_number, items_per_page, ['user__username', 'room__name'])
        },
    ]
    app_list.append({'name': 'Accounts', 'app_label': 'accounts', 'models': accounts_models, 'icon': 'people'})

    # Catalog app
    from apps.catalog.admin import BookAdmin, BookCopyAdmin, AuthorAdmin, PublisherAdmin, FacultyAdmin, DepartmentAdmin, TopicAdmin, GenreAdmin
    catalog_models = [
        {
            'name': 'Books',
            'object_name': 'Book',
            'count': Book.objects.count(),
            'admin_url': reverse('admin:catalog_book_changelist'),
            'add_url': reverse('admin:catalog_book_add'),
            'icon': 'book',
            'fields': ['title', 'isbn', 'publisher', 'publication_date', 'pages'],
            'actions': get_admin_actions(BookAdmin),
            'items': _get_paginated_items(Book, search_query, page_number, items_per_page, ['title', 'isbn', 'publisher__name'])
        },
        {
            'name': 'Book Copies',
            'object_name': 'BookCopy',
            'count': BookCopy.objects.count(),
            'admin_url': reverse('admin:catalog_bookcopy_changelist'),
            'add_url': reverse('admin:catalog_bookcopy_add'),
            'icon': 'book-half',
            'fields': ['book', 'barcode', 'condition', 'status'],
            'actions': get_admin_actions(BookCopyAdmin),
            'items': _get_paginated_items(BookCopy, search_query, page_number, items_per_page, ['book__title', 'barcode'])
        },
        {
            'name': 'Authors',
            'object_name': 'Author',
            'count': Author.objects.count(),
            'admin_url': reverse('admin:catalog_author_changelist'),
            'add_url': reverse('admin:catalog_author_add'),
            'icon': 'person',
            'fields': ['name', 'bio'],
            'actions': get_admin_actions(AuthorAdmin),
            'items': _get_paginated_items(Author, search_query, page_number, items_per_page, ['name'])
        },
        {
            'name': 'Publishers',
            'object_name': 'Publisher',
            'count': Publisher.objects.count(),
            'admin_url': reverse('admin:catalog_publisher_changelist'),
            'add_url': reverse('admin:catalog_publisher_add'),
            'icon': 'building',
            'fields': ['name', 'address', 'website'],
            'actions': get_admin_actions(PublisherAdmin),
            'items': _get_paginated_items(Publisher, search_query, page_number, items_per_page, ['name'])
        },
        {
            'name': 'Faculties',
            'object_name': 'Faculty',
            'count': Faculty.objects.count(),
            'admin_url': reverse('admin:catalog_faculty_changelist'),
            'add_url': reverse('admin:catalog_faculty_add'),
            'icon': 'building',
            'fields': ['name', 'description', 'code'],
            'actions': get_admin_actions(FacultyAdmin),
            'items': _get_paginated_items(Faculty, search_query, page_number, items_per_page, ['name', 'code'])
        },
        {
            'name': 'Departments',
            'object_name': 'Department',
            'count': Department.objects.count(),
            'admin_url': reverse('admin:catalog_department_changelist'),
            'add_url': reverse('admin:catalog_department_add'),
            'icon': 'diagram-3',
            'fields': ['name', 'faculty', 'code'],
            'actions': get_admin_actions(DepartmentAdmin),
            'items': _get_paginated_items(Department, search_query, page_number, items_per_page, ['name', 'faculty__name'])
        },
        {
            'name': 'Topics',
            'object_name': 'Topic',
            'count': Topic.objects.count(),
            'admin_url': reverse('admin:catalog_topic_changelist'),
            'add_url': reverse('admin:catalog_topic_add'),
            'icon': 'tags',
            'fields': ['name', 'department', 'code'],
            'actions': get_admin_actions(TopicAdmin),
            'items': _get_paginated_items(Topic, search_query, page_number, items_per_page, ['name', 'department__name'])
        },
        {
            'name': 'Genres',
            'object_name': 'Genre',
            'count': Genre.objects.count(),
            'admin_url': reverse('admin:catalog_genre_changelist'),
            'add_url': reverse('admin:catalog_genre_add'),
            'icon': 'tag',
            'fields': ['name', 'description'],
            'actions': get_admin_actions(GenreAdmin),
            'items': _get_paginated_items(Genre, search_query, page_number, items_per_page, ['name'])
        },
    ]
    app_list.append({'name': 'Catalog', 'app_label': 'catalog', 'models': catalog_models, 'icon': 'book'})

    # Circulation app
    from apps.circulation.admin import LoanAdmin, ReservationAdmin, FineAdmin, LoanRequestAdmin, AttendanceAdmin
    circulation_models = [
        {
            'name': 'Loans',
            'object_name': 'Loan',
            'count': Loan.objects.count(),
            'admin_url': reverse('admin:circulation_loan_changelist'),
            'add_url': None,
            'icon': 'arrow-left-right',
            'fields': ['user', 'book_copy', 'loan_date', 'due_date', 'status'],
            'actions': get_admin_actions(LoanAdmin),
            'items': _get_paginated_items(Loan, search_query, page_number, items_per_page, ['user__username', 'book_copy__book__title'])
        },
        {
            'name': 'Reservations',
            'object_name': 'Reservation',
            'count': Reservation.objects.count(),
            'admin_url': reverse('admin:circulation_reservation_changelist'),
            'add_url': None,
            'icon': 'bookmark',
            'fields': ['user', 'book', 'reservation_date', 'status'],
            'actions': get_admin_actions(ReservationAdmin),
            'items': _get_paginated_items(Reservation, search_query, page_number, items_per_page, ['user__username', 'book__title'])
        },
        {
            'name': 'Loan Requests',
            'object_name': 'LoanRequest',
            'count': LoanRequest.objects.count(),
            'admin_url': reverse('admin:circulation_loanrequest_changelist'),
            'add_url': None,
            'icon': 'clipboard-check',
            'fields': ['user', 'book_copy', 'request_date', 'status'],
            'actions': get_admin_actions(LoanRequestAdmin),
            'items': _get_paginated_items(LoanRequest, search_query, page_number, items_per_page, ['user__username', 'book_copy__book__title'])
        },
        {
            'name': 'Fines',
            'object_name': 'Fine',
            'count': Fine.objects.count(),
            'admin_url': reverse('admin:circulation_fine_changelist'),
            'add_url': None,
            'icon': 'cash',
            'fields': ['loan', 'amount', 'reason', 'status'],
            'actions': get_admin_actions(FineAdmin),
            'items': _get_paginated_items(Fine, search_query, page_number, items_per_page, ['loan__user__username', 'amount'])
        },
        {
            'name': 'Attendance',
            'object_name': 'Attendance',
            'count': Attendance.objects.count(),
            'admin_url': reverse('admin:circulation_attendance_changelist'),
            'add_url': reverse('admin:circulation_attendance_add'),
            'icon': 'person-check',
            'fields': ['user', 'full_name', 'check_in', 'check_out', 'status'],
            'actions': get_admin_actions(AttendanceAdmin),
            'items': _get_paginated_items(Attendance, search_query, page_number, items_per_page, ['full_name', 'user__username'])
        },
    ]
    app_list.append({'name': 'Circulation', 'app_label': 'circulation', 'models': circulation_models, 'icon': 'arrow-left-right'})

    # Blog app
    blog_models = []
    if BlogPost:
        blog_models.append({
            'name': 'Blog Posts',
            'object_name': 'BlogPost',
            'count': BlogPost.objects.count(),
            'admin_url': reverse('admin:blog_blogpost_changelist'),
            'add_url': reverse('admin:blog_blogpost_add'),
            'icon': 'newspaper',
            'fields': ['title', 'author', 'published_date', 'status'],
            'items': _get_paginated_items(BlogPost, search_query, page_number, items_per_page, ['title', 'author__username'])
        })
    blog_models.extend([
        {
            'name': 'Static Pages',
            'object_name': 'StaticPage',
            'count': StaticPage.objects.count(),
            'admin_url': reverse('admin:blog_staticpage_changelist'),
            'add_url': reverse('admin:blog_staticpage_add'),
            'icon': 'file-text',
            'fields': ['title', 'slug', 'is_active'],
            'items': _get_paginated_items(StaticPage, search_query, page_number, items_per_page, ['title', 'slug'])
        },
        {
            'name': 'Featured Content',
            'object_name': 'FeaturedContent',
            'count': FeaturedContent.objects.count(),
            'admin_url': reverse('admin:blog_featuredcontent_changelist'),
            'add_url': reverse('admin:blog_featuredcontent_add'),
            'icon': 'star',
            'fields': ['title', 'is_active', 'order'],
            'items': _get_paginated_items(FeaturedContent, search_query, page_number, items_per_page, ['title'])
        },
        {
            'name': 'News',
            'object_name': 'News',
            'count': News.objects.count(),
            'admin_url': reverse('admin:blog_news_changelist'),
            'add_url': reverse('admin:blog_news_add'),
            'icon': 'megaphone',
            'fields': ['title', 'author', 'published_date', 'status'],
            'items': _get_paginated_items(News, search_query, page_number, items_per_page, ['title', 'author__username'])
        },
    ])
    app_list.append({'name': 'Blog', 'app_label': 'blog', 'models': blog_models, 'icon': 'newspaper'})

    # Events app
    events_models = [
        {
            'name': 'Events',
            'object_name': 'Event',
            'count': Event.objects.count(),
            'admin_url': reverse('admin:events_event_changelist'),
            'add_url': reverse('admin:events_event_add'),
            'icon': 'calendar-event',
            'fields': ['title', 'date', 'time', 'location', 'organizer'],
            'items': _get_paginated_items(Event, search_query, page_number, items_per_page, ['title', 'organizer__username'])
        },
        {
            'name': 'Event Registrations',
            'object_name': 'EventRegistration',
            'count': EventRegistration.objects.count(),
            'admin_url': reverse('admin:events_eventregistration_changelist'),
            'add_url': None,
            'icon': 'person-plus',
            'fields': ['event', 'user'],
            'items': _get_paginated_items(EventRegistration, search_query, page_number, items_per_page, ['event__title', 'user__username'])
        },
    ]
    app_list.append({'name': 'Events', 'app_label': 'events', 'models': events_models, 'icon': 'calendar-event'})

    # Repository app
    from apps.repository.models import DocumentPermission, DocumentPermissionRequest
    repository_models = [
        {
            'name': 'Collections',
            'object_name': 'Collection',
            'count': Collection.objects.count(),
            'admin_url': reverse('admin:repository_collection_changelist'),
            'add_url': reverse('admin:repository_collection_add'),
            'icon': 'collection',
            'fields': ['name', 'description', 'curator'],
            'items': _get_paginated_items(Collection, search_query, page_number, items_per_page, ['name', 'curator__username'])
        },
        {
            'name': 'Documents',
            'object_name': 'Document',
            'count': Document.objects.count(),
            'admin_url': reverse('admin:repository_document_changelist'),
            'add_url': reverse('admin:repository_document_add'),
            'icon': 'file-earmark',
            'fields': ['title', 'authors', 'upload_date', 'access_level', 'uploaded_by'],
            'items': _get_paginated_items(Document, search_query, page_number, items_per_page, ['title', 'uploaded_by__username'])
        },
        {
            'name': 'Document Permission Requests',
            'object_name': 'DocumentPermissionRequest',
            'count': DocumentPermissionRequest.objects.count(),
            'admin_url': reverse('repository:review_requests'),
            'add_url': None,
            'icon': 'clipboard-check',
            'fields': ['document', 'user', 'status', 'requested_at'],
            'items': _get_paginated_items(DocumentPermissionRequest, search_query, page_number, items_per_page, ['document__title', 'user__username'])
        },
        {
            'name': 'Document Permissions',
            'object_name': 'DocumentPermission',
            'count': DocumentPermission.objects.count(),
            'admin_url': reverse('admin:repository_documentpermission_changelist'),
            'add_url': reverse('admin:repository_documentpermission_add'),
            'icon': 'shield-check',
            'fields': ['document', 'user', 'granted', 'granted_by', 'granted_at'],
            'items': _get_paginated_items(DocumentPermission, search_query, page_number, items_per_page, ['document__title', 'user__username'])
        },
    ]
    app_list.append({'name': 'Repository', 'app_label': 'repository', 'models': repository_models, 'icon': 'file-earmark'})

    # Collect data for all modules (limited for performance)
    context = {
        # Welcome and stats
        'user_count': total_users,
        'book_count': total_books,
        'document_count': document_count,
        'event_count': event_count,
        'active_users': active_users,
        'overdue_loans': overdue_loans,
        'pending_reservations': pending_reservations,
        'storage_usage': storage_usage,
        'recent_actions': recent_actions,

        # User management
        'pending_staff': pending_staff,
        'recent_users': recent_users,
        'total_users': total_users,
        'active_users_count': active_users,
        'staff_users': staff_users,
        'faculty_users': faculty_users,
        'student_users': student_users,
        'total_books': total_books,
        'active_loans': active_loans,

        # Apps and models with full CRUD data
        'app_list': app_list,
        'search_query': search_query,

        # Legacy data for backward compatibility
        'study_rooms': StudyRoom.objects.all()[:20],
        'study_room_bookings': StudyRoomBooking.objects.order_by('-created_at')[:20],
        'blog_posts': BlogPost.objects.order_by('-created_at')[:20] if BlogPost else [],
        'static_pages': StaticPage.objects.all()[:20],
        'featured_content': FeaturedContent.objects.order_by('-created_at')[:20],
        'news_items': News.objects.order_by('-created_at')[:20],
        'authors': Author.objects.order_by('-created_at')[:20],
        'publishers': Publisher.objects.all()[:20],
        'faculties': Faculty.objects.all(),
        'departments': Department.objects.all()[:20],
        'topics': Topic.objects.all()[:20],
        'genres': Genre.objects.all(),
        'books': Book.objects.order_by('-created_at')[:20],
        'book_copies': BookCopy.objects.order_by('-created_at')[:20],
        'loans': Loan.objects.order_by('-created_at')[:20],
        'reservations': Reservation.objects.order_by('-created_at')[:20],
        'loan_requests': LoanRequest.objects.order_by('-created_at')[:20],
        'fines': Fine.objects.order_by('-created_at')[:20],
        'attendance_records': Attendance.objects.order_by('-created_at')[:20],
        'events': Event.objects.order_by('-created_at')[:20],
        'event_registrations': EventRegistration.objects.order_by('-created_at')[:20],
        'collections': Collection.objects.all()[:20],
        'documents': Document.objects.order_by('-upload_date')[:20],
    }
    return render(request, 'accounts/admin_dashboard.html', context)


def _get_paginated_items(model_class, search_query, page_number, items_per_page, search_fields):
    """Helper function to get paginated items with search functionality."""
    from django.core.paginator import Paginator
    from django.db.models import Q

    queryset = model_class.objects.all()

    # Apply search filter
    if search_query:
        q_objects = Q()
        for field in search_fields:
            q_objects |= Q(**{f"{field}__icontains": search_query})
        queryset = queryset.filter(q_objects)

    # Apply ordering
    if hasattr(model_class, '_meta') and model_class._meta.ordering:
        queryset = queryset.order_by(*model_class._meta.ordering)
    else:
        queryset = queryset.order_by('-id')

    # Paginate
    paginator = Paginator(queryset, items_per_page)
    try:
        page_obj = paginator.page(page_number)
    except:
        page_obj = paginator.page(1)

    return page_obj


@login_required
@user_passes_test(lambda u: u.is_superuser)
def approve_staff(request, user_id):
    """Approve staff registration and activate account immediately."""
    user = get_object_or_404(LibraryUser, id=user_id, membership_type='staff', is_staff_approved=False)

    if request.method == 'POST':
        user.is_staff_approved = True
        user.email_verified = True  # Mark email as verified since admin approved
        user.is_active = True  # Activate account immediately
        user.save()

        # Send notification email that account is active
        try:
            send_mail(
                subject="Staff Registration Approved - Account Activated",
                message=f"Dear {user.get_full_name()},\n\n"
                       f"Your staff registration has been approved by the library administration.\n\n"
                       f"Your account has been activated and you can now log in to the library system.\n\n"
                       f"Username: {user.username}\n\n"
                       f"You can access your account at: {request.build_absolute_uri(reverse('accounts:login'))}\n\n"
                       f"Best regards,\nRamat Library Administration",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to send approval notification email to {user.username}: {e}")
            messages.warning(request, f'Staff registration approved, but email notification failed. Please inform the user manually.')

        messages.success(request, f'Staff registration for {user.get_full_name()} has been approved. Account activated and notification email sent.')
        return redirect('accounts:admin_dashboard')

    return render(request, 'accounts/approve_staff.html', {'user': user})


@login_required
@user_passes_test(lambda u: u.is_superuser)
def reject_staff(request, user_id):
    """Reject staff registration."""
    user = get_object_or_404(LibraryUser, id=user_id, membership_type='staff', is_staff_approved=False)

    if request.method == 'POST':
        reason = request.POST.get('reason', 'Registration rejected by administrator')

        # Send rejection email
        try:
            send_mail(
                subject="Staff Registration Update",
                message=f"Dear {user.get_full_name()},\n\n"
                       f"We regret to inform you that your staff registration has been rejected.\n\n"
                       f"Reason: {reason}\n\n"
                       f"If you have questions, please contact the library administration.\n\n"
                       f"Best regards,\nRamat Library Administration",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to send rejection email to {user.username}: {e}")
            messages.warning(request, f'Staff registration rejected, but email notification failed. Please inform the user manually.')

        # Delete the user account
        user.delete()

        messages.info(request, f'Staff registration for {user.get_full_name()} has been rejected and removed.')
        return redirect('accounts:admin_dashboard')

    return render(request, 'accounts/reject_staff.html', {'user': user})


@login_required
@user_passes_test(lambda u: u.is_superuser)
def user_role_management(request):
    """Manage user roles - change between staff and student."""
    # Get users who are either staff or students
    users = LibraryUser.objects.filter(
        membership_type__in=['staff', 'student']
    ).order_by('last_name', 'first_name')

    context = {
        'users': users,
    }
    return render(request, 'accounts/user_role_management.html', context)


@login_required
@user_passes_test(lambda u: u.is_superuser)
def change_user_role(request, user_id):
    """Change a user's role between staff and student."""
    user = get_object_or_404(LibraryUser, id=user_id, membership_type__in=['staff', 'student'])

    if request.method == 'POST':
        current_role = user.membership_type
        new_role = 'student' if current_role == 'staff' else 'staff'

        # Update the user's membership type
        user.membership_type = new_role

        # If changing to staff, ensure they are approved
        if new_role == 'staff':
            user.is_staff_approved = True

        # If changing from staff to student, clear staff approval
        elif current_role == 'staff':
            user.is_staff_approved = False

        user.save()

        # Send notification email
        try:
            send_mail(
                subject="User Role Updated",
                message=f"Dear {user.get_full_name()},\n\n"
                       f"Your user role has been updated from {current_role.title()} to {new_role.title()}.\n\n"
                       f"If you have any questions, please contact the library administration.\n\n"
                       f"Best regards,\nRamat Library Administration",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to send role change email to {user.username}: {e}")
            messages.warning(request, f'User role updated, but email notification failed. Please inform the user manually.')

        messages.success(request, f'{user.get_full_name()}\'s role has been changed from {current_role.title()} to {new_role.title()}.')
        return redirect('accounts:user_role_management')

    return redirect('accounts:user_role_management')


@login_required
def profile_view(request):
    if request.method == 'POST':
        form = LibraryUserChangeForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')

            # Check if this is an AJAX request
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': 'Profile updated successfully!'})
            else:
                return redirect('accounts:profile')
        else:
            # Handle AJAX request with errors
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': 'Please correct the errors and try again.'})
    else:
        form = LibraryUserChangeForm(instance=request.user)
    return render(request, 'accounts/profile.html', {'form': form})


class StaffDirectoryView(ListView):
    model = LibraryUser
    template_name = 'accounts/staff_directory.html'
    context_object_name = 'staff_members'
    paginate_by = 20

    def get_queryset(self):
        return LibraryUser.objects.filter(
            membership_type__in=['faculty', 'staff']
        ).order_by('last_name', 'first_name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get department counts for staff members
        department_counts = LibraryUser.objects.filter(
            membership_type__in=['faculty', 'staff']
        ).exclude(department__isnull=True).exclude(department='').values('department').annotate(
            count=Count('department')
        ).order_by('department')

        # Create a dictionary mapping department names to counts
        dept_counts_dict = {item['department']: item['count'] for item in department_counts}

        # Map template department names to actual department values
        context['department_counts'] = {
            'circulation': dept_counts_dict.get('Circulation', 0),
            'reference': dept_counts_dict.get('Reference', 0),
            'technical': dept_counts_dict.get('Technical', 0),
            'digital': dept_counts_dict.get('Digital', 0),
            'special_collections': dept_counts_dict.get('Special Collections', 0),
        }

        return context


def home_view(request):
    """Public home dashboard showing library overview, news, quick search, and promotional content."""
    # Featured books (most popular based on copies or recent)
    featured_books = Book.objects.active().prefetch_related('authors', 'genre')[:6]

    # Recent blog posts (safe if blog app isn't installed)
    if BlogPost is not None:
        recent_news = BlogPost.objects.filter(status='published').order_by('-published_date')[:3]
    else:
        recent_news = []

    # Upcoming events
    upcoming_events = Event.objects.filter(date__gte=timezone.now().date()).order_by('date', 'time')[:4]

    # Popular genres
    popular_genres = Genre.objects.prefetch_related('books').annotate(
        book_count=Count('books')
    ).order_by('-book_count')[:6]

    # Quick stats for overview
    total_books = Book.objects.active().count()
    total_documents = Document.objects.filter(access_level='open').count()

    context = {
        'featured_books': featured_books,
        'recent_news': recent_news,
        'upcoming_events': upcoming_events,
        'popular_genres': popular_genres,
        'total_books': total_books,
        'total_documents': total_documents,
    }
    return render(request, 'accounts/home.html', context)


def contact_view(request):
    """Public contact form for inquiries."""
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        message = request.POST.get('message')

        if name and email and message:
            # Send email to library
            full_message = f"From: {name} ({email})\n\nSubject: {subject}\n\nMessage:\n{message}"
            try:
                send_mail(
                    subject=f"Library Contact: {subject}",
                    message=full_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=['ramatlibrary@unimaid.edu.ng'],  # Update with actual email
                    fail_silently=False,
                )
                messages.success(request, 'Your message has been sent successfully!')
                return redirect('contact')
            except Exception as e:
                messages.error(request, 'Failed to send message. Please try again.')
        else:
            messages.error(request, 'Please fill in all required fields.')

    return render(request, 'accounts/contact.html')


def research_assistance_view(request):
    """Research assistance services page."""
    context = {
        'page_title': 'Research Assistance',
        'services': [
            {
                'title': 'Reference Services',
                'description': 'Get help with finding information, research strategies, and database searching.',
                'icon': 'bi-search'
            },
            {
                'title': 'Citation Help',
                'description': 'Learn proper citation styles and get assistance with bibliographies.',
                'icon': 'bi-bookmark-check'
            },
            {
                'title': 'Research Consultation',
                'description': 'Schedule one-on-one sessions with research librarians.',
                'icon': 'bi-person-lines-fill'
            },
            {
                'title': 'Database Training',
                'description': 'Workshops on using academic databases and research tools.',
                'icon': 'bi-pc-display'
            }
        ]
    }
    return render(request, 'accounts/research_assistance.html', context)


def interlibrary_loan_view(request):
    """Interlibrary loan services page."""
    context = {
        'page_title': 'Interlibrary Loan',
        'services': [
            {
                'title': 'Book Requests',
                'description': 'Request books not available in our collection from other libraries.',
                'icon': 'bi-book'
            },
            {
                'title': 'Article Delivery',
                'description': 'Get copies of journal articles delivered electronically.',
                'icon': 'bi-file-earmark-text'
            },
            {
                'title': 'Document Delivery',
                'description': 'Access materials from libraries worldwide.',
                'icon': 'bi-globe'
            }
        ]
    }
    return render(request, 'accounts/interlibrary_loan.html', context)


@login_required
def study_room_booking_view(request):
    """Study room booking page."""
    if request.method == 'POST':
        # Handle booking submission
        room_id = request.POST.get('room_type')
        date_str = request.POST.get('date')
        time_slot = request.POST.get('time')
        duration = int(request.POST.get('duration', 1))
        people = int(request.POST.get('people', 1))
        purpose = request.POST.get('purpose', '')

        try:
            room = StudyRoom.objects.get(id=room_id, is_active=True)
            booking_date = datetime.strptime(date_str, '%Y-%m-%d').date()

            # Parse time slot
            if time_slot == 'morning':
                start_time = time(8, 0)
                end_time = time(12, 0)
            elif time_slot == 'afternoon':
                start_time = time(12, 0)
                end_time = time(17, 0)
            elif time_slot == 'evening':
                start_time = time(17, 0)
                end_time = time(22, 0)
            elif time_slot == 'overnight':
                start_time = time(22, 0)
                end_time = time(8, 0)  # Next day
            else:
                raise ValueError("Invalid time slot")

            # Check if booking date is in the future
            today = timezone.now().date()
            if booking_date < today:
                messages.error(request, 'Cannot book rooms for past dates.')
                return redirect('accounts:study_room_booking')

            # Check capacity
            if people > room.capacity:
                messages.error(request, f'This room can only accommodate {room.capacity} people.')
                return redirect('accounts:study_room_booking')

            # Check availability - no overlapping bookings
            conflicting_bookings = StudyRoomBooking.objects.filter(
                room=room,
                date=booking_date,
                status__in=['pending', 'confirmed']
            ).filter(
                Q(start_time__lt=end_time, end_time__gt=start_time)
            )

            if conflicting_bookings.exists():
                messages.error(request, 'This room is not available for the selected time slot.')
                return redirect('accounts:study_room_booking')

            # Create booking
            booking = StudyRoomBooking.objects.create(
                user=request.user,
                room=room,
                date=booking_date,
                start_time=start_time,
                end_time=end_time,
                duration_hours=duration,
                number_of_people=people,
                purpose=purpose,
                status='pending'
            )

            messages.success(request, f'Your booking request for {room.name} has been submitted and is pending approval.')
            return redirect('accounts:study_room_booking')

        except StudyRoom.DoesNotExist:
            messages.error(request, 'Selected room is not available.')
        except ValueError as e:
            messages.error(request, str(e))
        except Exception as e:
            messages.error(request, 'An error occurred while processing your booking.')

        return redirect('accounts:study_room_booking')

    # GET request - show available rooms
    rooms = StudyRoom.objects.filter(is_active=True).order_by('name')

    # Add availability info for each room
    room_data = []
    today = timezone.now().date()

    for room in rooms:
        # Count today's bookings
        today_bookings = StudyRoomBooking.objects.filter(
            room=room,
            date=today,
            status__in=['pending', 'confirmed']
        ).count()

        # Determine availability text based on room type and current bookings
        if room.room_type == 'individual':
            availability = 'Available 24/7'
        elif room.room_type == 'group':
            availability = '8 AM - 10 PM'
        else:  # presentation
            availability = 'By reservation only'

        room_data.append({
            'id': room.id,
            'name': room.name,
            'capacity': f'1-{room.capacity} people' if room.capacity <= 2 else f'{room.capacity} people',
            'features': room.features,
            'availability': availability,
            'today_bookings': today_bookings
        })

    context = {
        'page_title': 'Study Room Booking',
        'rooms': room_data
    }
    return render(request, 'accounts/study_room_booking.html', context)


def digital_resources_view(request):
    """Digital resources and online databases page."""
    context = {
        'page_title': 'Digital Resources',
        'resources': [
            {
                'name': 'JSTOR',
                'description': 'Academic journals and books in various disciplines.',
                'type': 'Database',
                'access': 'On-campus & VPN'
            },
            {
                'name': 'IEEE Xplore',
                'description': 'Engineering and technology research papers.',
                'type': 'Database',
                'access': 'On-campus & VPN'
            },
            {
                'name': 'PubMed',
                'description': 'Biomedical literature database.',
                'type': 'Database',
                'access': 'Free access'
            },
            {
                'name': 'EbscoHost',
                'description': 'Academic journals and research databases.',
                'type': 'Database',
                'access': 'On-campus & VPN'
            },
            {
                'name': 'Google Scholar',
                'description': 'Search across scholarly literature.',
                'type': 'Search Engine',
                'access': 'Free access'
            },
            {
                'name': 'Microsoft Academic',
                'description': 'Research papers and academic content.',
                'type': 'Search Engine',
                'access': 'Free access'
            }
        ]
    }
    return render(request, 'accounts/digital_resources.html', context)


def library_resources_view(request):
    """Unified library resources overview page explaining physical vs digital libraries."""
    context = {
        'page_title': 'Library Resources',
        'physical_resources': {
            'title': 'Physical Library Collection',
            'description': 'Browse and borrow physical books from our extensive collection',
            'features': [
                '50,000+ physical books across all disciplines',
                'Current loans and reservations system',
                'Study rooms and reading areas',
                'Reference and research assistance',
                'Interlibrary loan services'
            ],
            'icon': 'bi-book',
            'url': '/catalog/',
            'color': 'primary'
        },
        'digital_resources': {
            'title': 'Digital Library & Repository',
            'description': 'Access digital documents, theses, and research papers online 24/7',
            'features': [
                '10,000+ digital documents and theses',
                'Open access research repository',
                'Institutional research outputs',
                '24/7 online access from anywhere',
                'Download and citation tools'
            ],
            'icon': 'bi-file-earmark-text',
            'url': '/repository/',
            'color': 'success'
        },
        'external_databases': {
            'title': 'Online Databases & Journals',
            'description': 'Premium academic databases and research tools',
            'features': [
                'JSTOR, IEEE Xplore, PubMed, and more',
                'Full-text academic journals',
                'Research databases and archives',
                'Citation and reference tools',
                'On-campus and VPN access'
            ],
            'icon': 'bi-globe',
            'url': '/accounts/digital-resources/',
            'color': 'info'
        }
    }
    return render(request, 'accounts/library_resources.html', context)


def privacy_policy_view(request):
    """Privacy policy page."""
    context = {
        'page_title': 'Privacy Policy'
    }
    return render(request, 'accounts/privacy_policy.html', context)


def terms_of_use_view(request):
    """Terms of use page."""
    context = {
        'page_title': 'Terms of Use'
    }
    return render(request, 'accounts/terms_of_use.html', context)


def open_access_view(request):
    """Open access resources and academic databases page."""
    context = {
        'page_title': 'Open Access Resources',
        'academic_databases': [
            {'name': 'Google Scholar', 'url': 'https://scholar.google.com/', 'description': 'Search across scholarly literature'},
            {'name': 'National Academies', 'url': 'https://www.nationalacademies.org/', 'description': 'Research and publications'},
            {'name': 'Scientific Research Publishing', 'url': 'https://www.scirp.org/', 'description': 'Open access journals'},
            {'name': 'SpringerOpen', 'url': 'https://www.springernature.com/gp/open-science/journals-books/journals', 'description': 'Open access journals'},
            {'name': 'ScienceDirect', 'url': 'https://www.sciencedirect.com/', 'description': 'Scientific database'},
            {'name': 'Jstor', 'url': 'https://www.jstor.org/action/showLogin', 'description': 'Digital library'},
            {'name': 'Omics International', 'url': 'https://www.omicsonline.org/', 'description': 'Open access publishing'},
            {'name': 'Oxford Academics', 'url': 'https://academic.oup.com/', 'description': 'Academic publishing'},
            {'name': 'Wiley', 'url': 'https://onlinelibrary.wiley.com/', 'description': 'Scientific publishing'},
            {'name': 'National Virtual Library Of Nigeria', 'url': 'https://virtuall.nln.gov.ng/accounts/login', 'description': 'National library resources'},
            {'name': 'OARE', 'url': 'https://www.unep.org/topics/environment-under-review/digital-library/online-access-research-environment-oare', 'description': 'Environmental research'},
            {'name': 'Ebrary', 'url': 'https://ebrary.net/', 'description': 'E-book platform'},
            {'name': 'Project Muse', 'url': 'https://muse.jhu.edu/', 'description': 'Humanities and social sciences'},
            {'name': 'Legalpedia', 'url': 'https://legalpediaonline.com/', 'description': 'Legal research'},
            {'name': 'Emerald Insight', 'url': 'http://library.cusat.ac.in/index.php/emerald-list-of-journals', 'description': 'Business and management'},
        ],
        'additional_databases': [
            {'name': 'World Bank e-Library', 'url': 'https://elibrary.worldbank.org', 'description': 'World Bank publications'},
            {'name': 'MathSciNet', 'url': 'https://mathscinet.ams.org', 'description': 'Mathematics research (subscription required)'},
            {'name': 'EconBiz', 'url': 'https://www.econbiz.de', 'description': 'Economics research'},
            {'name': 'African Journals Online (AJOL)', 'url': 'https://www.ajol.info', 'description': 'African scholarly journals'},
            {'name': 'Annual Reviews', 'url': 'https://www.annualreviews.org', 'description': 'Review articles (some free)'},
            {'name': 'Aluka', 'url': 'https://www.jstor.org', 'description': 'African cultural heritage'},
            {'name': 'BioOne', 'url': 'https://bioone.org', 'description': 'Biological sciences (subscription)'},
            {'name': 'DATAD', 'url': 'https://datad.org', 'description': 'African theses and dissertations'},
            {'name': 'Oxford English Dictionary', 'url': 'https://www.oed.com', 'description': 'Dictionary (subscription)'},
            {'name': 'Oxford Reference Online', 'url': 'https://www.oxfordreference.com', 'description': 'Reference works (subscription)'},
            {'name': 'APS Journals', 'url': 'https://journals.aps.org', 'description': 'Physics journals'},
            {'name': 'GEM Portal', 'url': 'https://www.gemconsortium.org', 'description': 'Entrepreneurship research'},
            {'name': 'World Bank Publications', 'url': 'https://openknowledge.worldbank.org', 'description': 'Development research'},
            {'name': 'Directory of Open Access Journals (DOAJ)', 'url': 'https://doaj.org', 'description': 'Open access journals directory'},
            {'name': 'SAGE Journals', 'url': 'https://journals.sagepub.com', 'description': 'Social sciences (mixed access)'},
            {'name': 'Directory of Open Access Books (DOAB)', 'url': 'https://www.doabooks.org', 'description': 'Open access books'},
            {'name': 'Bentham Open', 'url': 'https://benthamopen.com', 'description': 'Open access publishing'},
            {'name': 'The Journal of Research Practice', 'url': 'https://jrp.icaap.org', 'description': 'Research methodology'},
            {'name': 'edX', 'url': 'https://www.edx.org', 'description': 'Online courses'},
            {'name': 'The WomanStats Project', 'url': 'https://www.womanstats.org', 'description': 'Gender research'},
            {'name': 'Strategies for Online Teaching', 'url': 'https://teachonline.ca', 'description': 'Educational resources'},
            {'name': 'MedlinePlus', 'url': 'https://medlineplus.gov', 'description': 'Health information'},
            {'name': 'The NTS Library', 'url': 'https://www.ntsb.gov/investigations/Pages/library.aspx', 'description': 'Transportation safety'},
            {'name': 'World eBook Library', 'url': 'https://www.worldebooklibrary.org', 'description': 'E-book collection (subscription)'},
            {'name': 'J-Gate Medical / PubMed', 'url': 'J-Gate: https://jgateplus.com, PubMed: https://pubmed.ncbi.nlm.nih.gov', 'description': 'Medical literature'},
            {'name': 'Wiley Online Library', 'url': 'https://onlinelibrary.wiley.com', 'description': 'Scientific publishing (mixed access)'},
        ]
    }
    return render(request, 'accounts/open_access.html', context)


def open_resources_view(request):
    """Open educational resources and free e-book sites."""
    context = {
        'page_title': 'Open Resources',
        'ebook_sites': [
            {'name': 'American Institute of Mathematics (AIM)', 'url': 'https://aimath.org/textbooks', 'description': 'Mathematics textbooks'},
            {'name': 'Booksee', 'url': 'https://booksee.org', 'description': 'Book collection (availability varies)'},
            {'name': 'Bookboon', 'url': 'https://bookboon.com', 'description': 'Free textbooks'},
            {'name': 'Connexions (OpenStax CNX)', 'url': 'https://cnx.org', 'description': 'Open textbooks'},
            {'name': 'FreeBooks4Doctors', 'url': 'https://www.freebooks4doctors.com', 'description': 'Medical books'},
            {'name': 'Free Book Center', 'url': 'https://www.freebookcentre.net', 'description': 'Book collection'},
            {'name': 'IntechOpen (INTECH)', 'url': 'https://www.intechopen.com', 'description': 'Open access books'},
            {'name': 'IT eBooks', 'url': 'https://it-ebooks.info', 'description': 'Technology books'},
            {'name': 'Living Books About Life', 'url': 'https://www.livingbooksaboutlife.org', 'description': 'Biology books'},
            {'name': 'National Academies Press', 'url': 'https://nap.nationalacademies.org', 'description': 'Research publications'},
            {'name': 'NCBI Bookshelf', 'url': 'https://www.ncbi.nlm.nih.gov/books', 'description': 'Biomedical books'},
            {'name': 'Open Access Textbooks', 'url': 'https://openaccesstextbooks.org', 'description': 'Textbook collection'},
            {'name': 'Open Textbook Library', 'url': 'https://open.umn.edu/opentextbooks', 'description': 'Peer-reviewed textbooks'},
            {'name': 'Oxfam Digital Library', 'url': 'https://policy-practice.oxfam.org/resources', 'description': 'Development resources'},
            {'name': 'Project Gutenberg', 'url': 'https://www.gutenberg.org', 'description': 'Classic literature'},
        ]
    }
    return render(request, 'accounts/open_resources.html', context)


def virtual_tour_view(request):
    """Virtual tour gallery showing library spaces."""
    # For now, static images from media directory
    # In real implementation, could have a model for tour images
    context = {
        'tour_images': [
            'images/library_front.jpg',
            'images/reading_room.jpg',
            'images/study_area.jpg',
            'images/computer_lab.jpg',
        ]
    }
    return render(request, 'accounts/virtual_tour.html', context)


def delete_item(request, app_label, model_name, item_id):
    """Generic delete view for all models accessible through admin dashboard.

    Handles AJAX requests by returning JSON and normal requests with redirects/messages.
    """
    # Permission check: allow only authenticated superusers
    if not request.user.is_authenticated or not request.user.is_superuser:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'Authentication/permission required'}, status=401)
        return redirect(f"{reverse('accounts:login')}?next={request.path}")

    if request.method != 'POST':
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)
        messages.error(request, 'Method not allowed')
        return redirect('accounts:admin_dashboard')

    try:
        # Get the model class dynamically
        model_class = django_apps.get_model(app_label, model_name)
        item = get_object_or_404(model_class, id=item_id)

        # Get display name for success message
        display_name = str(item)

        # Attempt deletion - let Django handle integrity constraints
        item.delete()

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': f'{model_class._meta.verbose_name} "{display_name}" deleted'})

        messages.success(request, f'{model_class._meta.verbose_name} "{display_name}" has been deleted successfully.')
        return redirect('accounts:admin_dashboard')

    except Exception as e:
        # Handle specific database integrity errors
        error_message = str(e)
        if 'foreign key constraint' in error_message.lower() or 'integrity constraint' in error_message.lower():
            user_msg = f'Cannot delete {model_name} because it is referenced by other records. Please remove the related data first.'
        else:
            user_msg = f'Error deleting {model_name}: {error_message}'

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': user_msg}, status=400)

        messages.error(request, user_msg)
        return redirect('accounts:admin_dashboard')


def confirm_email(request, token):
    """Handle email confirmation for staff registration - no login required."""
    from .models import EmailConfirmationToken

    try:
        confirmation_token = EmailConfirmationToken.objects.get(token=token)

        if confirmation_token.is_expired():
            messages.error(request, 'This confirmation link has expired. Please contact the administrator.')
            return redirect('accounts:login')

        user = confirmation_token.user

        if user.email_verified:
            messages.info(request, 'Your email has already been confirmed. You can now log in.')
            return redirect('accounts:login')

        # Mark email as verified and activate account
        user.email_verified = True
        user.save()

        # Delete the used token
        confirmation_token.delete()

        # Show success page instead of redirecting
        return render(request, 'accounts/email_confirmed.html', {'user': user})

    except EmailConfirmationToken.DoesNotExist:
        messages.error(request, 'Invalid confirmation link.')
        return redirect('accounts:login')


def download_user_qr(request, user_id):
    """Download QR code for a user."""
    user = get_object_or_404(LibraryUser, id=user_id)
    if not user.qr_code:
        # Generate QR code if it doesn't exist
        user.generate_qr_code()
        user.save()

    # Return the QR code file
    response = HttpResponse(user.qr_code, content_type='image/png')
    response['Content-Disposition'] = f'attachment; filename="user_{user.id}_qr.png"'
    return response


def get_form_view(request, app_label, model_name, item_id=None):
    """AJAX view to get form HTML for create/edit operations.

    Returns JSON for AJAX clients and handles authentication/permission errors gracefully.
    """
    from django.forms import modelform_factory

    # Permission check
    if not request.user.is_authenticated or not request.user.is_superuser:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'Authentication/permission required'}, status=401)
        return redirect(f"{reverse('accounts:login')}?next={request.path}")

    try:
        model_class = django_apps.get_model(app_label, model_name)

        # Use improved form creation logic
        exclude_fields = []
        model_fields = [f.name for f in model_class._meta.get_fields() if not f.many_to_many]

        # Exclude complex fields that might cause issues
        for field in model_class._meta.get_fields():
            if field.many_to_many or field.one_to_many:
                exclude_fields.append(field.name)
            elif hasattr(field, 'related_model') and field.related_model == model_class:
                # Self-referencing fields can be problematic
                exclude_fields.append(field.name)

        # For now, use a basic set of fields to avoid complex relationships
        if model_name in ['LibraryUser', 'Book', 'BookCopy', 'Author', 'Publisher']:
            # Use specific fields for known models
            if model_name == 'LibraryUser':
                FormClass = LibraryUserChangeForm
            else:
                FormClass = modelform_factory(model_class, exclude=exclude_fields)
        else:
            # For other models, try to exclude problematic fields
            FormClass = modelform_factory(model_class, exclude=exclude_fields)

        if item_id:
            instance = get_object_or_404(model_class, id=item_id)
            form = FormClass(instance=instance)
        else:
            form = FormClass()

        # Render form to HTML
        form_html = ''
        for field in form:
            form_html += f'<div class="mb-3">{field.label_tag()}{field}{field.errors}</div>'

        return JsonResponse({
            'success': True,
            'form_html': form_html
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
@user_passes_test(lambda u: u.is_superuser)
def execute_action(request):
    """Execute admin actions on selected items."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)

    try:
        import json
        data = json.loads(request.body)
        app_label = data.get('app_label')
        model_name = data.get('model_name')
        action_name = data.get('action_name')
        selected_items = data.get('selected_items', [])

        if not all([app_label, model_name, action_name, selected_items]):
            return JsonResponse({'success': False, 'error': 'Missing required parameters'})

        # Get the model and admin class
        model_class = django_apps.get_model(app_label, model_name)

        # Import admin classes dynamically
        if app_label == 'accounts':
            from .admin import LibraryUserAdmin, StudyRoomAdmin, StudyRoomBookingAdmin
            admin_classes = {
                'LibraryUser': LibraryUserAdmin,
                'StudyRoom': StudyRoomAdmin,
                'StudyRoomBooking': StudyRoomBookingAdmin,
            }
        elif app_label == 'catalog':
            from apps.catalog.admin import BookAdmin, BookCopyAdmin, AuthorAdmin, PublisherAdmin, FacultyAdmin, DepartmentAdmin, TopicAdmin, GenreAdmin
            admin_classes = {
                'Book': BookAdmin,
                'BookCopy': BookCopyAdmin,
                'Author': AuthorAdmin,
                'Publisher': PublisherAdmin,
                'Faculty': FacultyAdmin,
                'Department': DepartmentAdmin,
                'Topic': TopicAdmin,
                'Genre': GenreAdmin,
            }
        elif app_label == 'circulation':
            from apps.circulation.admin import LoanAdmin, ReservationAdmin, FineAdmin, LoanRequestAdmin, AttendanceAdmin
            admin_classes = {
                'Loan': LoanAdmin,
                'Reservation': ReservationAdmin,
                'Fine': FineAdmin,
                'LoanRequest': LoanRequestAdmin,
                'Attendance': AttendanceAdmin,
            }
        else:
            return JsonResponse({'success': False, 'error': 'Admin class not found for this model'})

        admin_class = admin_classes.get(model_name)
        if not admin_class:
            return JsonResponse({'success': False, 'error': 'Admin class not found'})

        # Get the action method
        action_method = getattr(admin_class, action_name, None)
        if not action_method:
            return JsonResponse({'success': False, 'error': 'Action method not found'})

        # Create a mock request and queryset
        from django.contrib.admin.sites import AdminSite
        from django.contrib.admin.views.main import ChangeList
        from django.db.models import QuerySet

        # Create queryset with selected items
        queryset = model_class.objects.filter(id__in=selected_items)

        # Create mock admin site and request
        admin_site = AdminSite()
        mock_request = request

        # Create an instance of the admin class
        admin_instance = admin_class(model_class, admin_site)

        # Execute the action
        try:
            result = action_method(admin_instance, mock_request, queryset)
            # Some actions return HttpResponseRedirect, others return None
            return JsonResponse({
                'success': True,
                'message': f'Action "{action_name}" executed successfully on {len(selected_items)} items.'
            })
        except Exception as action_error:
            return JsonResponse({
                'success': False,
                'error': f'Action execution failed: {str(action_error)}'
            })

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON data'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@user_passes_test(lambda u: u.is_superuser)
def import_data_view(request, app_label, model_name):
    """Import data for a specific model using django-import-export."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)

    try:
        model_class = django_apps.get_model(app_label, model_name)

        # Get the resource class from the admin
        if app_label == 'catalog' and model_name == 'Book':
            from apps.catalog.admin import BookAdmin, BookResource
            resource_class = BookResource
        else:
            # For other models, try to create a basic resource
            from import_export import resources
            resource_class = resources.ModelResource
            resource_class.Meta.model = model_class

        # Create resource instance
        resource = resource_class()

        # Get the uploaded file
        import_file = request.FILES.get('import_file')
        if not import_file:
            return JsonResponse({'success': False, 'error': 'No file uploaded'})

        # Import the data
        from import_export.results import Result
        from io import StringIO
        import csv

        # Read file content
        file_content = import_file.read().decode('utf-8')
        input_format = request.POST.get('input_format', 'csv')

        if input_format == 'csv':
            dataset = resource.get_import_dataset(StringIO(file_content), 'csv')
        else:
            return JsonResponse({'success': False, 'error': 'Unsupported format'})

        # Perform dry run first
        result = resource.import_data(dataset, dry_run=True)

        if result.has_errors():
            errors = []
            for error in result.base_errors:
                errors.append(str(error))
            for line, row_errors in result.row_errors():
                for error in row_errors:
                    errors.append(f'Row {line}: {error.error}')
            return JsonResponse({'success': False, 'error': 'Import validation failed', 'details': errors})

        # Perform actual import
        result = resource.import_data(dataset, dry_run=False)

        return JsonResponse({
            'success': True,
            'message': f'Successfully imported {result.totals.get("new", 0)} new records, updated {result.totals.get("update", 0)} records.'
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@user_passes_test(lambda u: u.is_superuser)
def export_data_view(request, app_label, model_name):
    """Export data for a specific model using django-import-export."""
    try:
        model_class = django_apps.get_model(app_label, model_name)

        # Get the resource class from the admin
        if app_label == 'catalog' and model_name == 'Book':
            from apps.catalog.admin import BookAdmin, BookResource
            resource_class = BookResource
        else:
            # For other models, try to create a basic resource
            from import_export import resources
            resource_class = resources.ModelResource
            resource_class.Meta.model = model_class

        # Create resource instance
        resource = resource_class()

        # Get queryset (apply any filters from request)
        queryset = model_class.objects.all()

        # Export data
        from import_export.formats import CSV
        format_class = CSV()
        dataset = resource.export(queryset)
        export_data = format_class.export_data(dataset)

        # Return as downloadable file
        response = HttpResponse(export_data, content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{model_name}_export.csv"'
        return response

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
