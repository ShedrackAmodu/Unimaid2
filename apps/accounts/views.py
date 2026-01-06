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
from apps.blog.models import BlogPost
from apps.events.models import Event
from apps.repository.models import Document


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

    # Recent blog posts
    recent_news = BlogPost.objects.filter(status='published').order_by('-published_date')[:3]

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
