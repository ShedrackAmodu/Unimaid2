from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
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
    if request.method == 'POST':
        form = LibraryUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            if user.membership_type == 'staff':
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
                               f"Email: {user.email}\n"
                               f"Department: {user.department or 'Not specified'}\n"
                               f"Faculty ID: {user.faculty_id or 'Not specified'}\n\n"
                               f"Please review and approve/reject this registration in the admin dashboard.",
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[settings.DEFAULT_FROM_EMAIL],  # Send to admin email
                        fail_silently=False,
                    )
                except Exception as e:
                    # Log error but don't fail registration
                    print(f"Failed to send admin notification email: {e}")

                messages.info(request, 'Registration submitted for approval. You will receive an email once your account is approved.')
                return redirect('accounts:login')
            else:
                # Non-staff users are active immediately
                login(request, user)
                messages.success(request, 'Registration successful!')
                return redirect('accounts:dashboard')
    else:
        form = LibraryUserCreationForm()
    return render(request, 'accounts/register.html', {'form': form})


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
    """Admin dashboard for user management and approvals."""
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

    # System stats (simplified)
    from apps.catalog.models import Book
    from apps.circulation.models import Loan
    total_books = Book.objects.active().count()
    active_loans = Loan.objects.filter(status='active').count()

    context = {
        'pending_staff': pending_staff,
        'recent_users': recent_users,
        'total_users': total_users,
        'active_users': active_users,
        'staff_users': staff_users,
        'faculty_users': faculty_users,
        'student_users': student_users,
        'total_books': total_books,
        'active_loans': active_loans,
    }
    return render(request, 'accounts/admin_dashboard.html', context)


@login_required
@user_passes_test(lambda u: u.is_superuser)
def approve_staff(request, user_id):
    """Approve staff registration."""
    user = get_object_or_404(LibraryUser, id=user_id, membership_type='staff', is_staff_approved=False)

    if request.method == 'POST':
        user.is_staff_approved = True
        user.is_active = True
        user.save()

        # Send approval email
        try:
            send_mail(
                subject="Staff Registration Approved",
                message=f"Dear {user.get_full_name()},\n\n"
                       f"Your staff registration has been approved. You can now log in to your account.\n\n"
                       f"Username: {user.username}\n\n"
                       f"Best regards,\nRamat Library Administration",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
        except Exception as e:
            print(f"Failed to send approval email: {e}")

        messages.success(request, f'Staff registration for {user.get_full_name()} has been approved.')
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
            print(f"Failed to send rejection email: {e}")

        # Delete the user account
        user.delete()

        messages.info(request, f'Staff registration for {user.get_full_name()} has been rejected and removed.')
        return redirect('accounts:admin_dashboard')

    return render(request, 'accounts/reject_staff.html', {'user': user})


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
