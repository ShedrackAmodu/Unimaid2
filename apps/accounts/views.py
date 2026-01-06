from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.views.generic import ListView
from django.db.models import Count
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from .models import LibraryUser
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
    if request.method == 'POST':
        form = LibraryUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Registration successful!')
            return redirect('accounts:dashboard')
    else:
        form = LibraryUserCreationForm()
    return render(request, 'accounts/register.html', {'form': form})


@login_required
def dashboard_view(request):
    user = request.user
    context = {
        'user': user,
        'current_loans': user.loans.filter(status='active')[:5],  # Show recent loans
        'reservations': user.reservations.filter(status='active')[:5],
        'recent_fines': user.loans.filter(fines__status='unpaid').distinct()[:5],
    }
    return render(request, 'accounts/dashboard.html', context)


@login_required
def profile_view(request):
    if request.method == 'POST':
        form = LibraryUserChangeForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('accounts:profile')
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


def study_room_booking_view(request):
    """Study room booking page."""
    context = {
        'page_title': 'Study Room Booking',
        'rooms': [
            {
                'name': 'Individual Study Room',
                'capacity': '1-2 people',
                'features': ['Quiet space', 'Power outlets', 'WiFi'],
                'availability': 'Available 24/7'
            },
            {
                'name': 'Group Study Room',
                'capacity': '4-6 people',
                'features': ['Whiteboard', 'Projector', 'Power outlets', 'WiFi'],
                'availability': '8 AM - 10 PM'
            },
            {
                'name': 'Presentation Room',
                'capacity': '10-15 people',
                'features': ['Projector', 'Sound system', 'Whiteboard', 'WiFi'],
                'availability': 'By reservation only'
            }
        ]
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
